"""
Riwayat controller — query list laporan (dengan filter) dan rekap.
Pakai text() untuk query kompleks dengan filter dinamis.
"""
import logging
from sqlalchemy import text
from database.session import get_session


def get_riwayat_laporan(
    section_id=None, shift_name=None, date_from=None, date_to=None
) -> list:
    base_query = """
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
    params = {}

    if section_id is not None:
        base_query += " AND dr.section_id = :section_id"
        params["section_id"] = section_id

    if shift_name is not None:
        base_query += " AND sh.name = :shift_name"
        params["shift_name"] = shift_name

    if date_from is not None:
        base_query += " AND dr.date >= :date_from"
        params["date_from"] = date_from

    if date_to is not None:
        base_query += " AND dr.date <= :date_to"
        params["date_to"] = date_to

    base_query += """
        GROUP BY dr.id, dr.date, sec.name, sh.name, dr.coordinator, dr.status
        ORDER BY dr.date DESC, dr.id DESC
    """

    with get_session() as session:
        rows = session.execute(text(base_query), params).fetchall()

    return [
        {
            "id":          r[0],
            "date":        str(r[1]),
            "section":     r[2],
            "shift":       r[3],
            "coordinator": r[4],
            "jml_masalah": int(r[5]) if r[5] is not None else 0,
            "status":      r[6],
        }
        for r in rows
    ]


def get_monthly_productivity(section_id, bulan: int, tahun: int) -> dict:
    sec_filter = " AND dr.section_id = :section_id" if section_id is not None else ""
    params: dict = {"bulan": bulan, "tahun": tahun}
    if section_id is not None:
        params["section_id"] = section_id

    with get_session() as session:
        r = session.execute(text(f"""
            SELECT COALESCE(SUM(s.total_hours), 0),
                   COALESCE(SUM(s.preparation_min / 60.0), 0),
                   COALESCE(SUM(s.other_min / 60.0), 0),
                   COUNT(dr.id)
            FROM daily_report dr
            JOIN shift s ON s.id = dr.shift_id
            WHERE EXTRACT(MONTH FROM dr.date) = :bulan
              AND EXTRACT(YEAR  FROM dr.date) = :tahun {sec_filter}
        """), params).fetchone()

        total_hour   = float(r[0] or 0)
        prep_hour    = float(r[1] or 0)
        other_hour   = float(r[2] or 0)
        report_count = int(r[3]   or 0)

        r2 = session.execute(text(f"""
            SELECT COALESCE(SUM(
                CASE WHEN dp.ot_2h  THEN 2.0  ELSE 0 END +
                CASE WHEN dp.ot_3h  THEN 3.0  ELSE 0 END +
                CASE WHEN dp.ot_11h THEN 11.0 ELSE 0 END
            ), 0)
            FROM (SELECT DISTINCT ON (report_id) report_id, ot_2h, ot_3h, ot_11h
                  FROM daily_production) dp
            JOIN daily_report dr ON dr.id = dp.report_id
            WHERE EXTRACT(MONTH FROM dr.date) = :bulan
              AND EXTRACT(YEAR  FROM dr.date) = :tahun {sec_filter}
        """), params).fetchone()
        total_hour += float((r2 or [0])[0] or 0)

        cat_rows = session.execute(text(f"""
            SELECT COALESCE(pcg.name, 'Others') AS grp,
                   COALESCE(pc.name,  'Others') AS cat,
                   COALESCE(SUM(pr.loss_time), 0)
            FROM problem_record pr
            LEFT JOIN problem_category pc  ON pc.id  = pr.category_id
            LEFT JOIN problem_group pcg    ON pcg.id = pc.group_id
            JOIN daily_report dr ON dr.id = pr.report_id
            WHERE EXTRACT(MONTH FROM dr.date) = :bulan
              AND EXTRACT(YEAR  FROM dr.date) = :tahun {sec_filter}
            GROUP BY grp, cat
            ORDER BY grp, cat
        """), params).fetchall()
        categories = [
            {"group": r[0], "name": r[1], "hours": float(r[2] or 0)}
            for r in cat_rows
        ]

        r3 = session.execute(text(f"""
            SELECT COALESCE(SUM(
                CASE WHEN a.keterangan ~ '^[0-9]+(\\.[0-9]+)?$'
                     THEN a.keterangan::FLOAT ELSE 0 END
            ), 0)
            FROM absen a
            JOIN daily_report dr ON dr.id = a.report_id
            WHERE EXTRACT(MONTH FROM dr.date) = :bulan
              AND EXTRACT(YEAR  FROM dr.date) = :tahun {sec_filter}
        """), params).fetchone()
        absence_hour = float((r3 or [0])[0] or 0)

        r4 = session.execute(text(f"""
            SELECT COALESCE(SUM(ic.lost_hr), 0)
            FROM inhouse_claim ic
            JOIN daily_report dr ON dr.id = ic.report_id
            WHERE EXTRACT(MONTH FROM dr.date) = :bulan
              AND EXTRACT(YEAR  FROM dr.date) = :tahun {sec_filter}
        """), params).fetchone()
        quality_hour = float((r4 or [0])[0] or 0)

    loss_hour    = sum(c["hours"] for c in categories)
    process_hour = max(total_hour - prep_hour - other_hour - loss_hour - absence_hour - quality_hour, 0.0)

    return {
        "total_hour":   total_hour,
        "process_hour": process_hour,
        "prep_hour":    prep_hour,
        "other_hour":   other_hour,
        "absence_hour": absence_hour,
        "quality_hour": quality_hour,
        "categories":   categories,
        "report_count": report_count,
    }


def get_production_volume(section_id: int, bulan: int, tahun: int) -> dict:
    import calendar

    with get_session() as session:
        models = [
            r[0] for r in session.execute(text(
                "SELECT model_name FROM shop_model WHERE section_id = :sid ORDER BY model_name"
            ), {"sid": section_id}).fetchall()
        ]

        shifts = [
            r[0] for r in session.execute(text(
                "SELECT name FROM shift ORDER BY id"
            )).fetchall()
        ]

        vol_rows = session.execute(text("""
            SELECT dp.model, sh.name, EXTRACT(DAY FROM dr.date)::int,
                   SUM(dp.actual_unit)
            FROM daily_production dp
            JOIN daily_report dr ON dr.id = dp.report_id
            JOIN shift sh ON sh.id = dr.shift_id
            WHERE dr.section_id = :sid
              AND EXTRACT(MONTH FROM dr.date) = :bulan
              AND EXTRACT(YEAR  FROM dr.date) = :tahun
            GROUP BY dp.model, sh.name, EXTRACT(DAY FROM dr.date)
            ORDER BY dp.model, sh.name
        """), {"sid": section_id, "bulan": bulan, "tahun": tahun}).fetchall()

    data: dict = {}
    totals: dict = {}
    for model, shift_name, day, unit in vol_rows:
        key = (model, shift_name)
        if key not in data:
            data[key]   = {}
            totals[key] = 0
        data[key][day]  = int(unit or 0)
        totals[key]    += int(unit or 0)

    return {
        "models": models,
        "shifts": shifts,
        "days":   calendar.monthrange(tahun, bulan)[1],
        "data":   data,
        "totals": totals,
    }


def get_ng_pending(section_id, date_from, date_to) -> dict:
    """Query inhouse claim berstatus NG dan PENDING."""
    sec_filter = " AND dr.section_id = :section_id" if section_id is not None else ""
    params: dict = {"date_from": date_from, "date_to": date_to}
    if section_id is not None:
        params["section_id"] = section_id

    select_cols = """
        ic.tanggal, ic.model, ic.op_no_st, ic.item, ic.qty,
        ic.penyebab, ic.tindakan, ic.faktor, ic.stop_hr, ic.lost_hr
    """

    with get_session() as session:
        ng_rows = session.execute(text(f"""
            SELECT {select_cols}, ic.status
            FROM inhouse_claim ic
            JOIN daily_report dr ON dr.id = ic.report_id
            WHERE dr.date BETWEEN :date_from AND :date_to
              AND UPPER(ic.status) = 'NG' {sec_filter}
            ORDER BY ic.tanggal DESC, ic.id DESC
        """), params).fetchall()

        pending_rows = session.execute(text(f"""
            SELECT {select_cols}
            FROM inhouse_claim ic
            JOIN daily_report dr ON dr.id = ic.report_id
            WHERE dr.date BETWEEN :date_from AND :date_to
              AND UPPER(ic.status) = 'PENDING' {sec_filter}
            ORDER BY ic.tanggal DESC, ic.id DESC
        """), params).fetchall()

    def _to_dict_ng(r):
        return {
            "tanggal": r[0], "model": r[1] or "", "op_no_st": r[2] or "",
            "item": r[3] or "", "qty": float(r[4] or 0),
            "penyebab": r[5] or "", "tindakan": r[6] or "", "faktor": r[7] or "",
            "stop_hr": float(r[8] or 0), "lost_hr": float(r[9] or 0),
            "status": r[10] or "",
        }

    def _to_dict_pending(r):
        return {
            "tanggal": r[0], "model": r[1] or "", "op_no_st": r[2] or "",
            "item": r[3] or "", "qty": float(r[4] or 0),
            "penyebab": r[5] or "", "tindakan": r[6] or "", "faktor": r[7] or "",
            "stop_hr": float(r[8] or 0), "lost_hr": float(r[9] or 0),
        }

    return {
        "ng":      [_to_dict_ng(r)      for r in ng_rows],
        "pending": [_to_dict_pending(r) for r in pending_rows],
    }


def get_display_line_stop(section_id, bulan, tahun, factor=None) -> dict:
    """Query rekap stop & loss time per problem category (untuk tab rekap)."""
    sec_filter = " AND dr.section_id = :section_id" if section_id is not None else ""
    params: dict = {"bulan": bulan, "tahun": tahun}
    if section_id is not None:
        params["section_id"] = section_id

    with get_session() as session:
        r = session.execute(text(f"""
            SELECT COALESCE(SUM(s.total_hours), 0)
            FROM daily_report dr
            JOIN shift s ON s.id = dr.shift_id
            WHERE EXTRACT(MONTH FROM dr.date) = :bulan
              AND EXTRACT(YEAR  FROM dr.date) = :tahun {sec_filter}
        """), params).fetchone()
        total_hour = float((r or [0])[0] or 0)

        r2 = session.execute(text(f"""
            SELECT COALESCE(SUM(
                CASE WHEN dp.ot_2h  THEN 2.0  ELSE 0 END +
                CASE WHEN dp.ot_3h  THEN 3.0  ELSE 0 END +
                CASE WHEN dp.ot_11h THEN 11.0 ELSE 0 END
            ), 0)
            FROM daily_production dp
            JOIN daily_report dr ON dr.id = dp.report_id
            WHERE EXTRACT(MONTH FROM dr.date) = :bulan
              AND EXTRACT(YEAR  FROM dr.date) = :tahun {sec_filter}
        """), params).fetchone()
        total_hour += float((r2 or [0])[0] or 0)

        extra = ""
        params2 = dict(params)
        if factor and factor != "Semua":
            extra = " AND pc.name = :factor"
            params2["factor"] = factor

        detail_rows = session.execute(text(f"""
            SELECT
                dr.date, pr.ra_number, pr.description, pr.cause,
                pr.corrective_action,
                COALESCE(pc.name, 'Others') AS factor,
                COALESCE(pr.loss_time, 0),
                COALESCE(pr.down_time, 0)
            FROM problem_record pr
            JOIN daily_report dr ON dr.id = pr.report_id
            LEFT JOIN problem_category pc ON pc.id = pr.category_id
            WHERE EXTRACT(MONTH FROM dr.date) = :bulan
              AND EXTRACT(YEAR  FROM dr.date) = :tahun {sec_filter} {extra}
            ORDER BY dr.date, pr.id
        """), params2).fetchall()

        summary_rows = session.execute(text(f"""
            SELECT
                COALESCE(pc.name, 'Others') AS factor,
                COUNT(pr.id),
                COALESCE(SUM(pr.loss_time), 0),
                COALESCE(SUM(pr.down_time), 0)
            FROM problem_record pr
            JOIN daily_report dr ON dr.id = pr.report_id
            LEFT JOIN problem_category pc ON pc.id = pr.category_id
            WHERE EXTRACT(MONTH FROM dr.date) = :bulan
              AND EXTRACT(YEAR  FROM dr.date) = :tahun {sec_filter}
            GROUP BY factor ORDER BY factor
        """), params).fetchall()

    details = [
        {
            "date":               str(r[0]),
            "ra_number":          r[1] or "",
            "description":        r[2] or "",
            "cause":              r[3] or "",
            "corrective_action":  r[4] or "",
            "factor":             r[5] or "",
            "loss_time":          float(r[6] or 0),
            "down_time":          float(r[7] or 0),
        }
        for r in detail_rows
    ]

    summary = [
        {
            "factor":    r[0],
            "count":     int(r[1] or 0),
            "loss_time": float(r[2] or 0),
            "down_time": float(r[3] or 0),
        }
        for r in summary_rows
    ]

    return {
        "total_hour": total_hour,
        "details":    details,
        "summary":    summary,
    }
