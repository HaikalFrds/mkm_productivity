from modules.db_auth import get_connection


def get_all_sections() -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM section ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception:
        raise
    finally:
        conn.close()


def get_riwayat_laporan(
    section_id=None, shift_name=None, date_from=None, date_to=None
) -> list:
    conn = get_connection()
    try:
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
    except Exception:
        raise
    finally:
        conn.close()


def get_detail_laporan(report_id: int) -> tuple:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT dr.id, dr.date, sec.name, sh.name,
                   dr.coordinator, dr.approved_by, dr.checked_by, dr.status
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
            return None, [], [], [], [], []
        header = {
            "id": hdr[0], "date": str(hdr[1]), "section": hdr[2],
            "shift": hdr[3], "coordinator": hdr[4],
            "approved_by": hdr[5], "checked_by": hdr[6], "status": hdr[7],
        }

        cur.execute(
            """
            SELECT model, plan_unit, actual_unit, plan_whour, actual_whour,
                   ot_2h, ot_3h, ot_11h
            FROM daily_production
            WHERE report_id = %s
            ORDER BY id
            """,
            (report_id,),
        )
        produksi = [
            {
                "model":        r[0],
                "plan_unit":    float(r[1]) if r[1] is not None else 0.0,
                "actual_unit":  float(r[2]) if r[2] is not None else 0.0,
                "plan_whour":   float(r[3]) if r[3] is not None else 0.0,
                "actual_whour": float(r[4]) if r[4] is not None else 0.0,
                "ot_2h":        float(r[5]) if r[5] is not None else 0.0,
                "ot_3h":        float(r[6]) if r[6] is not None else 0.0,
                "ot_11h":       float(r[7]) if r[7] is not None else 0.0,
            }
            for r in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT pr.ra_number, pc.name, pr.description, pr.cause,
                   pr.corrective_action, pr.pic,
                   pr.start_time, pr.end_time, pr.down_time, pr.loss_time
            FROM problem_record pr
            LEFT JOIN problem_category pc ON pc.id = pr.category_id
            WHERE pr.report_id = %s
            ORDER BY pr.id
            """,
            (report_id,),
        )
        catatan = [
            {
                "ra_number":        r[0], "category": r[1], "description": r[2],
                "cause":            r[3], "corrective_action": r[4], "pic": r[5],
                "start_time":       str(r[6]) if r[6] else "",
                "end_time":         str(r[7]) if r[7] else "",
                "down_time":        float(r[8]) if r[8] is not None else 0.0,
                "loss_time":        float(r[9]) if r[9] is not None else 0.0,
            }
            for r in cur.fetchall()
        ]

        cur.execute(
            "SELECT role, plan_count, act_count FROM manpower WHERE report_id = %s ORDER BY id",
            (report_id,),
        )
        manpower = [
            {
                "role": r[0] or "",
                "plan": int(r[1]) if r[1] is not None else 0,
                "act":  int(r[2]) if r[2] is not None else 0,
            }
            for r in cur.fetchall()
        ]

        cur.execute(
            "SELECT no, nama, nik, shop, keterangan FROM absen WHERE report_id = %s ORDER BY no",
            (report_id,),
        )
        absen = [
            {
                "no":         r[0],
                "nama":       r[1] or "",
                "nik":        r[2] or "",
                "shop":       r[3] or "",
                "keterangan": r[4] or "",
            }
            for r in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT model, op_no_st, item, qty, satuan,
                   penyebab, tindakan, faktor, stop_hr, lost_hr, status
            FROM inhouse_claim
            WHERE report_id = %s
            ORDER BY id
            """,
            (report_id,),
        )
        inhouse_claim = [
            {
                "model":    r[0] or "", "op_no_st": r[1] or "", "item":    r[2] or "",
                "qty":      float(r[3]) if r[3] is not None else 0.0,
                "satuan":   r[4] or "", "penyebab": r[5] or "", "tindakan": r[6] or "",
                "faktor":   r[7] or "",
                "stop_hr":  float(r[8])  if r[8]  is not None else 0.0,
                "lost_hr":  float(r[9])  if r[9]  is not None else 0.0,
                "status":   r[10] or "",
            }
            for r in cur.fetchall()
        ]

        cur.close()
        return header, produksi, catatan, manpower, absen, inhouse_claim
    except Exception:
        raise
    finally:
        conn.close()


def hapus_laporan(report_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM manpower       WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM absen          WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM inhouse_claim  WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM problem_record WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM daily_production WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM pending_part    WHERE report_id = %s", (report_id,))
        cur.execute("DELETE FROM daily_report   WHERE id = %s",         (report_id,))
        conn.commit()
        cur.close()
        return True, f"Laporan #{report_id} berhasil dihapus."
    except Exception as e:
        try:
            conn.rollback()
        finally:
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

        # 2. Insert ke daily_report
        cur.execute("""
            INSERT INTO daily_report
                (user_id, shift_id, section_id, date, coordinator,
                 approved_by, checked_by, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft')
            RETURNING id
        """, (
            user_id,
            shift_id,
            section_id,
            header["tanggal"],
            header["koordinator"],
            header["approved_by"],
            header["checked_by"],
        ))
        report_id = cur.fetchone()[0]

        # 3. Insert baris produksi ke daily_production
        plan_wh   = header.get("plan_whour")   or 0
        actual_wh = header.get("actual_whour") or 0
        for p in produksi:
            if not p.get("model"):
                continue
            cur.execute("""
                INSERT INTO daily_production
                    (report_id, model, plan_unit, actual_unit, plan_whour, actual_whour,
                     ot_2h, ot_3h, ot_11h)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                report_id,
                p["model"],
                p.get("plan_unit")   or 0,
                p.get("actual_unit") or 0,
                plan_wh,
                actual_wh,
                p.get("ot_2h")  or 0,
                p.get("ot_3h")  or 0,
                p.get("ot_11h") or 0,
            ))

        # 4. Insert catatan masalah
        for c in catatan:
            if not c["deskripsi"]:
                continue
            cur.execute(
                "SELECT id FROM problem_category WHERE name = %s LIMIT 1",
                (c["kategori"],)
            )
            cat_row = cur.fetchone()
            category_id = cat_row[0] if cat_row else None

            cur.execute("""
                INSERT INTO problem_record
                    (report_id, category_id, ra_number, description, cause,
                     corrective_action, pic, start_time, end_time,
                     down_time, loss_time, date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                report_id,
                category_id,
                c["nomor_ra"]  or None,
                c["deskripsi"] or None,
                c["penyebab"]  or None,
                c["tindakan"]  or None,
                c["pic"]       or None,
                c["start_time"] or None,
                c["end_time"]   or None,
                c.get("down_time") or 0.0,
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
                ic["tanggal"]   or None,
                ic["model"]     or None,
                ic["op_no_st"]  or None,
                ic["item"]      or None,
                ic["qty"]       or 0,
                ic["satuan"]    or None,
                ic["penyebab"]  or None,
                ic["tindakan"]  or None,
                ic["faktor"]    or None,
                ic["stop_hr"]   or 0,
                ic["lost_hr"]   or 0,
                ic["status"]    or None,
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
                ab["nama"]        or None,
                ab["nik"]         or None,
                ab["shop"]        or None,
                ab["keterangan"]  or None,
            ))

        conn.commit()
        cur.close()
        return True, f"Laporan berhasil disimpan! (ID: {report_id})"

    except Exception as e:
        try:
            conn.rollback()
        finally:
            conn.close()
        return False, f"Gagal menyimpan laporan: {str(e)}"
