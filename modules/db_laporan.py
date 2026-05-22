from modules.db_auth import get_connection


def get_all_sections() -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM section ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_riwayat_laporan(
    section_id=None, shift_name=None, date_from=None, date_to=None
) -> list:
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT
            dr.id,
            dr.date,
            sec.name AS section,
            sh.name  AS shift,
            dr.coordinator,
            COUNT(pr.id) AS jml_masalah,
            dr.status
        FROM daily_report dr
        JOIN section sec ON sec.id = dr.section_id
        JOIN shift   sh  ON sh.id  = dr.shift_id
        LEFT JOIN problem_record pr ON pr.report_id = dr.id
        WHERE 1=1
    """
    params = []
    if section_id is not None:
        query += " AND dr.section_id = %s"
        params.append(section_id)
    if shift_name is not None:
        query += " AND sh.name = %s"
        params.append(shift_name)
    if date_from is not None:
        query += " AND dr.date >= %s"
        params.append(date_from)
    if date_to is not None:
        query += " AND dr.date <= %s"
        params.append(date_to)
    query += """
        GROUP BY dr.id, dr.date, sec.name, sh.name, dr.coordinator, dr.status
        ORDER BY dr.date DESC, dr.id DESC
    """
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": r[0],
            "date": str(r[1]),
            "section": r[2],
            "shift": r[3],
            "coordinator": r[4],
            "jml_masalah": int(r[5]) if r[5] is not None else 0,
            "status": r[6],
        }
        for r in rows
    ]


def get_detail_laporan(report_id: int) -> tuple:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT dr.id, dr.date, sec.name, sh.name,
               dr.coordinator, dr.approved_by, dr.checked_by, dr.status,
               (SELECT plan_whour   FROM daily_production WHERE report_id = dr.id LIMIT 1),
               (SELECT actual_whour FROM daily_production WHERE report_id = dr.id LIMIT 1)
        FROM daily_report dr
        JOIN section sec ON sec.id = dr.section_id
        JOIN shift   sh  ON sh.id  = dr.shift_id
        WHERE dr.id = %s
        """,
        (report_id,),
    )
    hdr = cur.fetchone()
    if not hdr:
        cur.close()
        conn.close()
        return None, [], []
    header = {
        "id": hdr[0], "date": str(hdr[1]), "section": hdr[2],
        "shift": hdr[3], "coordinator": hdr[4],
        "approved_by": hdr[5], "checked_by": hdr[6], "status": hdr[7],
        "plan_whour": float(hdr[8]) if hdr[8] is not None else None,
        "actual_whour": float(hdr[9]) if hdr[9] is not None else None,
    }
    cur.execute(
        """
        SELECT model, plan_unit, reg_actual, ot_2h, ot_3h, ot_11h
        FROM daily_production
        WHERE report_id = %s
        ORDER BY id
        """,
        (report_id,),
    )
    produksi = [
        {
            "model": r[0],
            "plan_unit": float(r[1]) if r[1] is not None else 0.0,
            "reg_actual": float(r[2]) if r[2] is not None else 0.0,
            "ot_2h": float(r[3]) if r[3] is not None else 0.0,
            "ot_3h": float(r[4]) if r[4] is not None else 0.0,
            "ot_11h": float(r[5]) if r[5] is not None else 0.0,
        }
        for r in cur.fetchall()
    ]
    cur.execute(
        """
        SELECT pr.ra_number, pc.name, pr.description, pr.cause,
               pr.corrective_action, pr.pic,
               pr.start_time, pr.end_time, pr.loss_time
        FROM problem_record pr
        LEFT JOIN problem_category pc ON pc.id = pr.category_id
        WHERE pr.report_id = %s
        ORDER BY pr.id
        """,
        (report_id,),
    )
    catatan = [
        {
            "ra_number": r[0], "category": r[1], "description": r[2],
            "cause": r[3], "corrective_action": r[4], "pic": r[5],
            "start_time": str(r[6]) if r[6] else "",
            "end_time": str(r[7]) if r[7] else "",
            "loss_time": float(r[8]) if r[8] is not None else 0.0,
        }
        for r in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return header, produksi, catatan


def hapus_laporan(report_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM manpower WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM absen WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM inhouse_claim WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM problem_record WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM production_model WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM daily_report WHERE id = %s", (report_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, f"Laporan #{report_id} berhasil dihapus."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Gagal menghapus laporan: {e}"


def simpan_laporan_harian(
    user_id: int, header: dict, catatan: list, produksi: list,
    inhouse_claim: list = None, manpower: list = None, absen: list = None,
) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()

        # 1. Ambil shift_id dan section_id
        cur.execute("SELECT id FROM shift WHERE name = %s LIMIT 1", (header["shift"],))
        shift_row = cur.fetchone()
        if not shift_row:
            return False, f"Shift '{header['shift']}' tidak ditemukan di database"
        shift_id = shift_row[0]

        cur.execute("SELECT id FROM section WHERE name = %s LIMIT 1", (header["section"],))
        section_row = cur.fetchone()
        if not section_row:
            return False, f"Section '{header['section']}' tidak ditemukan di database"
        section_id = section_row[0]

        # 2. Insert ke daily_report (dengan plan_whour & actual_whour)
        cur.execute("""
            INSERT INTO daily_report
                (user_id, shift_id, section_id, date, coordinator,
                 approved_by, checked_by, plan_whour, actual_whour, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'draft')
            RETURNING id
        """, (
            user_id,
            shift_id,
            section_id,
            header["tanggal"],
            header["koordinator"],
            header["approved_by"],
            header["checked_by"],
            header.get("plan_whour"),
            header.get("actual_whour"),
        ))
        report_id = cur.fetchone()[0]

        # 3. Insert baris produksi (multi-model)
        for p in produksi:
            if not p.get("model"):
                continue
            cur.execute("""
                INSERT INTO production_model
                    (report_id, model, plan_unit, reg_actual, ot_2h, ot_3h, ot_11h)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                report_id,
                p["model"],
                p.get("plan_unit") or 0,
                p.get("reg_actual") or 0,
                p.get("ot_2h") or 0,
                p.get("ot_3h") or 0,
                p.get("ot_11h") or 0,
            ))

        # 4. Insert catatan masalah
        for c in catatan:
            if not c["deskripsi"]:
                continue

            # Ambil category_id
            cur.execute(
                "SELECT id FROM problem_category WHERE name = %s LIMIT 1",
                (c["kategori"],)
            )
            cat_row = cur.fetchone()
            category_id = cat_row[0] if cat_row else None

            cur.execute("""
                INSERT INTO problem_record
                    (report_id, category_id, ra_number, description, cause,
                     corrective_action, pic, start_time, end_time, loss_time, date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                report_id,
                category_id,
                c["nomor_ra"] or None,
                c["deskripsi"] or None,
                c["penyebab"] or None,
                c["tindakan"] or None,
                c["pic"] or None,
                c["start_time"] or None,
                c["end_time"] or None,
                c["loss_time"] or 0.0,
                header["tanggal"],
            ))

        # 5. Insert inhouse claim
        for ic in (inhouse_claim or []):
            cur.execute("""
                INSERT INTO inhouse_claim
                    (report_id, tanggal, model, op_no_st, item, qty, satuan,
                     penyebab, tindakan, faktor, stop_hr, lost_hr, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                report_id,
                ic["tanggal"] or None,
                ic["model"] or None,
                ic["op_no_st"] or None,
                ic["item"] or None,
                ic["qty"] or 0,
                ic["satuan"] or None,
                ic["penyebab"] or None,
                ic["tindakan"] or None,
                ic["faktor"] or None,
                ic["stop_hr"] or 0,
                ic["lost_hr"] or 0,
                ic["status"] or None,
            ))

        # 6. Insert manpower
        for mp in (manpower or []):
            cur.execute("""
                INSERT INTO manpower (report_id, role, plan_count, act_count)
                VALUES (%s, %s, %s, %s)
            """, (report_id, mp["role"] or None, mp["plan"] or 0, mp["act"] or 0))

        # 7. Insert absen
        for ab in (absen or []):
            cur.execute("""
                INSERT INTO absen (report_id, no, nama, nik, shop, keterangan)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                report_id,
                ab["no"],
                ab["nama"] or None,
                ab["nik"] or None,
                ab["shop"] or None,
                ab["keterangan"] or None,
            ))

        conn.commit()
        cur.close()
        conn.close()
        return True, f"Laporan berhasil disimpan! (ID: {report_id})"

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Gagal menyimpan laporan: {str(e)}"