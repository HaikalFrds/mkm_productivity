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


def get_loss_time_per_bulan(section_id, tahun) -> list:
    """
    Return 12-item list (Jan–Des), tiap item:
    {
      'bulan': 1–12,
      'total_hour': float,
      'process_hour': float,
      'loss_by_category': {'Machine': 2.5, ...}
    }
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        sec = " AND dr.section_id = %s" if section_id is not None else ""
        p = [tahun] + ([section_id] if section_id else [])

        cur.execute(f"""
            SELECT EXTRACT(MONTH FROM dr.date)::int,
                   SUM(dp.actual_whour)
            FROM daily_production dp
            JOIN daily_report dr ON dr.id = dp.report_id
            WHERE EXTRACT(YEAR FROM dr.date) = %s {sec}
            GROUP BY 1
        """, p)
        hours = {r[0]: float(r[1] or 0) for r in cur.fetchall()}

        cur.execute(f"""
            SELECT EXTRACT(MONTH FROM dr.date)::int,
                   COALESCE(pc.name, 'Others'),
                   SUM(pr.loss_time)
            FROM problem_record pr
            JOIN daily_report dr ON dr.id = pr.report_id
            LEFT JOIN problem_category pc ON pc.id = pr.category_id
            WHERE EXTRACT(YEAR FROM dr.date) = %s {sec}
            GROUP BY 1, 2
        """, p)
        loss_map: dict[int, dict] = {}
        for bulan, kat, val in cur.fetchall():
            loss_map.setdefault(bulan, {})[kat] = float(val or 0)

        cur.close()
        result = []
        for m in range(1, 13):
            total = hours.get(m, 0.0)
            lbc   = loss_map.get(m, {})
            loss_total   = sum(lbc.values())
            process_hour = max(total - loss_total, 0.0)
            result.append({
                "bulan":            m,
                "total_hour":       total,
                "process_hour":     process_hour,
                "loss_by_category": lbc,
            })
        return result
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
        conn.rollback()
        return False, f"Gagal menghapus laporan: {e}"
    finally:
        conn.close()


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
            return False, f"Shop '{header['section']}' tidak ditemukan di database"
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
        conn.rollback()
        return False, f"Gagal menyimpan laporan: {str(e)}"
    finally:
        conn.close()


# =============================================================================
# MASTER DATA — SECTION CRUD
# =============================================================================

def tambah_section(nama: str) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM section WHERE LOWER(name) = LOWER(%s) LIMIT 1", (nama,))
        if cur.fetchone():
            return False, f"Shop '{nama}' sudah ada."
        cur.execute("INSERT INTO section (name) VALUES (%s)", (nama,))
        conn.commit()
        cur.close()
        return True, f"Shop '{nama}' berhasil ditambahkan."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menambah shop: {e}"
    finally:
        conn.close()


def edit_section(section_id: int, nama: str) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM section WHERE LOWER(name) = LOWER(%s) AND id != %s LIMIT 1",
            (nama, section_id),
        )
        if cur.fetchone():
            return False, f"Shop '{nama}' sudah ada."
        cur.execute("UPDATE section SET name = %s WHERE id = %s", (nama, section_id))
        conn.commit()
        cur.close()
        return True, f"Shop berhasil diubah menjadi '{nama}'."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal mengubah shop: {e}"
    finally:
        conn.close()


def hapus_section(section_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM daily_report WHERE section_id = %s", (section_id,))
        count = cur.fetchone()[0]
        if count > 0:
            return False, f"Shop tidak bisa dihapus — digunakan oleh {count} laporan."
        cur.execute("DELETE FROM section WHERE id = %s", (section_id,))
        conn.commit()
        cur.close()
        return True, "Shop berhasil dihapus."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menghapus shop: {e}"
    finally:
        conn.close()


# =============================================================================
# MASTER DATA — USER CRUD
# =============================================================================

def get_all_users() -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, nik, name, role FROM "user" ORDER BY name')
        rows = cur.fetchall()
        cur.close()
        return [{"id": r[0], "nik": r[1], "name": r[2], "role": r[3]} for r in rows]
    except Exception:
        raise
    finally:
        conn.close()


def tambah_user(nik: str, nama: str, role: str, password_hash: str) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM "user" WHERE nik = %s LIMIT 1', (nik,))
        if cur.fetchone():
            return False, f"NIK '{nik}' sudah terdaftar."
        cur.execute(
            'INSERT INTO "user" (nik, name, role, password_hash) VALUES (%s, %s, %s, %s)',
            (nik, nama, role, password_hash),
        )
        conn.commit()
        cur.close()
        return True, f"User '{nama}' berhasil ditambahkan."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menambah user: {e}"
    finally:
        conn.close()


def reset_password_user(user_id: int, password_hash: str) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute('UPDATE "user" SET password_hash = %s WHERE id = %s', (password_hash, user_id))
        conn.commit()
        cur.close()
        return True, "Password berhasil direset."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal reset password: {e}"
    finally:
        conn.close()


def hapus_user(user_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM "user" WHERE id = %s', (user_id,))
        conn.commit()
        cur.close()
        return True, "User berhasil dihapus."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menghapus user: {e}"
    finally:
        conn.close()


# =============================================================================
# MASTER DATA — KATEGORI MASALAH (problem_category + problem_group)
# =============================================================================

def get_all_groups() -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM problem_group ORDER BY id")
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception:
        raise
    finally:
        conn.close()


def get_all_kategori() -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT pc.id, pc.group_id, pg.name AS group_name,
                   pc.code, pc.name, pc.order_num
            FROM problem_category pc
            JOIN problem_group pg ON pg.id = pc.group_id
            ORDER BY pc.group_id, pc.order_num, pc.id
        """)
        rows = cur.fetchall()
        cur.close()
        return [
            {"id": r[0], "group_id": r[1], "group_name": r[2],
             "code": r[3], "name": r[4], "order_num": r[5]}
            for r in rows
        ]
    except Exception:
        raise
    finally:
        conn.close()


def tambah_kategori(name: str, group_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM problem_category WHERE LOWER(name) = LOWER(%s) LIMIT 1",
            (name,),
        )
        if cur.fetchone():
            return False, f"Kategori '{name}' sudah ada."
        code = name.strip().upper().replace(" ", "_")
        cur.execute(
            "SELECT COALESCE(MAX(order_num), 0) + 1 FROM problem_category WHERE group_id = %s",
            (group_id,),
        )
        order_num = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO problem_category (group_id, code, name, order_num) VALUES (%s, %s, %s, %s)",
            (group_id, code, name, order_num),
        )
        conn.commit()
        cur.close()
        return True, f"Kategori '{name}' berhasil ditambahkan."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menambah kategori: {e}"
    finally:
        conn.close()


def edit_kategori(cat_id: int, name: str, group_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM problem_category WHERE LOWER(name) = LOWER(%s) AND id != %s LIMIT 1",
            (name, cat_id),
        )
        if cur.fetchone():
            return False, f"Kategori '{name}' sudah ada."
        cur.execute(
            "UPDATE problem_category SET name = %s, group_id = %s WHERE id = %s",
            (name, group_id, cat_id),
        )
        conn.commit()
        cur.close()
        return True, f"Kategori berhasil diubah menjadi '{name}'."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal mengubah kategori: {e}"
    finally:
        conn.close()


def hapus_kategori(cat_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM problem_record WHERE category_id = %s", (cat_id,))
        count = cur.fetchone()[0]
        if count > 0:
            return False, f"Kategori tidak bisa dihapus — digunakan oleh {count} catatan masalah."
        cur.execute("DELETE FROM problem_category WHERE id = %s", (cat_id,))
        conn.commit()
        cur.close()
        return True, "Kategori berhasil dihapus."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menghapus kategori: {e}"
    finally:
        conn.close()


# =============================================================================
# MASTER DATA — SHIFT
# =============================================================================

def ensure_shift_columns():
    """Tambah kolom baru ke tabel shift jika belum ada."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            ALTER TABLE shift
                ADD COLUMN IF NOT EXISTS preparation_min FLOAT DEFAULT 15,
                ADD COLUMN IF NOT EXISTS sholat_min      FLOAT DEFAULT 10
        """)
        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()
    finally:
        conn.close()


def get_all_shifts() -> list:
    ensure_shift_columns()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, start_time, end_time, total_hours,
                   COALESCE(preparation_min, 15), COALESCE(sholat_min, 10)
            FROM shift ORDER BY id
        """)
        rows = cur.fetchall()
        cur.close()
        return [
            {
                "id":              r[0],
                "name":            r[1],
                "start_time":      str(r[2])[:5] if r[2] else "",
                "end_time":        str(r[3])[:5] if r[3] else "",
                "total_hours":     float(r[4]) if r[4] is not None else 0.0,
                "preparation_min": float(r[5]) if r[5] is not None else 15.0,
                "sholat_min":      float(r[6]) if r[6] is not None else 10.0,
            }
            for r in rows
        ]
    except Exception:
        raise
    finally:
        conn.close()


def update_shift_working_hour(shift_id: int, working_hour: float) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE shift SET total_hours = %s WHERE id = %s", (working_hour, shift_id))
        conn.commit()
        cur.close()
        return True, "Working hour berhasil diperbarui."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal memperbarui working hour: {e}"
    finally:
        conn.close()


def tambah_shift(
    name: str, start_time: str, end_time: str,
    total_hours: float, preparation_min: float = 15.0, sholat_min: float = 10.0,
) -> tuple[bool, str]:
    ensure_shift_columns()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM shift WHERE LOWER(name) = LOWER(%s) LIMIT 1", (name,))
        if cur.fetchone():
            return False, f"Shift '{name}' sudah ada."
        cur.execute(
            """INSERT INTO shift (name, start_time, end_time, total_hours, preparation_min, sholat_min)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (name, start_time, end_time, total_hours, preparation_min, sholat_min),
        )
        conn.commit()
        cur.close()
        return True, f"Shift '{name}' berhasil ditambahkan."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menambah shift: {e}"
    finally:
        conn.close()


def edit_shift(
    shift_id: int, name: str, start_time: str, end_time: str,
    total_hours: float, preparation_min: float = 15.0, sholat_min: float = 10.0,
) -> tuple[bool, str]:
    ensure_shift_columns()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM shift WHERE LOWER(name) = LOWER(%s) AND id != %s LIMIT 1",
            (name, shift_id),
        )
        if cur.fetchone():
            return False, f"Shift '{name}' sudah ada."
        cur.execute(
            """UPDATE shift SET name=%s, start_time=%s, end_time=%s,
               total_hours=%s, preparation_min=%s, sholat_min=%s WHERE id=%s""",
            (name, start_time, end_time, total_hours, preparation_min, sholat_min, shift_id),
        )
        conn.commit()
        cur.close()
        return True, f"Shift berhasil diubah menjadi '{name}'."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal mengubah shift: {e}"
    finally:
        conn.close()


def hapus_shift(shift_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM daily_report WHERE shift_id = %s", (shift_id,))
        count = cur.fetchone()[0]
        if count > 0:
            return False, f"Shift tidak bisa dihapus — digunakan oleh {count} laporan."
        cur.execute("DELETE FROM shift WHERE id = %s", (shift_id,))
        conn.commit()
        cur.close()
        return True, "Shift berhasil dihapus."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menghapus shift: {e}"
    finally:
        conn.close()


# =============================================================================
# MASTER DATA — SHOP MODEL
# =============================================================================

def _ensure_shop_model_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shop_model (
            id           SERIAL PRIMARY KEY,
            section_id   INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE,
            model_name   VARCHAR(100) NOT NULL,
            working_hour FLOAT DEFAULT 0,
            UNIQUE(section_id, model_name)
        )
    """)
    cur.execute("""
        ALTER TABLE shop_model
            ADD COLUMN IF NOT EXISTS working_hour FLOAT DEFAULT 0
    """)


def get_models_by_section(section_id: int) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        _ensure_shop_model_table(cur)
        conn.commit()
        cur.execute(
            "SELECT id, model_name, working_hour FROM shop_model WHERE section_id = %s ORDER BY model_name",
            (section_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return [{"id": r[0], "model_name": r[1], "working_hour": float(r[2] or 0)} for r in rows]
    except Exception:
        raise
    finally:
        conn.close()


def tambah_shop_model(section_id: int, model_name: str, working_hour: float = 0.0) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        _ensure_shop_model_table(cur)
        cur.execute(
            "SELECT id FROM shop_model WHERE section_id = %s AND LOWER(model_name) = LOWER(%s) LIMIT 1",
            (section_id, model_name),
        )
        if cur.fetchone():
            return False, f"Model '{model_name}' sudah ada di shop ini."
        cur.execute(
            "INSERT INTO shop_model (section_id, model_name, working_hour) VALUES (%s, %s, %s)",
            (section_id, model_name, working_hour),
        )
        conn.commit()
        cur.close()
        return True, f"Model '{model_name}' berhasil ditambahkan."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menambah model: {e}"
    finally:
        conn.close()


def edit_shop_model(model_id: int, model_name: str, working_hour: float) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE shop_model SET model_name = %s, working_hour = %s WHERE id = %s",
            (model_name, working_hour, model_id),
        )
        conn.commit()
        cur.close()
        return True, f"Model '{model_name}' berhasil diubah."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal mengubah model: {e}"
    finally:
        conn.close()


def hapus_shop_model(model_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM shop_model WHERE id = %s", (model_id,))
        conn.commit()
        cur.close()
        return True, "Model berhasil dihapus."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menghapus model: {e}"
    finally:
        conn.close()
