"""
Analytics controller — query untuk halaman Visualisasi.
"""
from sqlalchemy import text
from database.session import get_session


def get_loss_time_per_bulan(section_id, tahun) -> list:
    """
    Return list 12 item (Jan–Des):
    { 'bulan', 'total_hour', 'process_hour', 'loss_by_category' }
    """
    sec_filter = " AND dr.section_id = :section_id" if section_id is not None else ""
    params: dict = {"tahun": tahun}
    if section_id is not None:
        params["section_id"] = section_id

    with get_session() as session:
        hour_rows = session.execute(text(f"""
            SELECT EXTRACT(MONTH FROM dr.date)::int,
                   SUM(s.total_hours),
                   SUM(s.preparation_min / 60.0),
                   SUM(s.other_min / 60.0)
            FROM daily_report dr
            JOIN shift s ON s.id = dr.shift_id
            WHERE EXTRACT(YEAR FROM dr.date) = :tahun {sec_filter}
            GROUP BY 1
        """), params).fetchall()

        hours: dict     = {}
        prep_map: dict  = {}
        other_map: dict = {}
        for r in hour_rows:
            hours[r[0]]     = float(r[1] or 0)
            prep_map[r[0]]  = float(r[2] or 0)
            other_map[r[0]] = float(r[3] or 0)

        loss_rows = session.execute(text(f"""
            SELECT EXTRACT(MONTH FROM dr.date)::int,
                   COALESCE(pc.name, 'Others'),
                   SUM(pr.loss_time)
            FROM problem_record pr
            JOIN daily_report dr ON dr.id = pr.report_id
            LEFT JOIN problem_category pc ON pc.id = pr.category_id
            WHERE EXTRACT(YEAR FROM dr.date) = :tahun {sec_filter}
            GROUP BY 1, 2
        """), params).fetchall()

        loss_map: dict = {}
        for bulan, kat, val in loss_rows:
            loss_map.setdefault(bulan, {})[kat] = float(val or 0)

    result = []
    for m in range(1, 13):
        total      = hours.get(m, 0.0)
        lbc        = loss_map.get(m, {})
        loss_total = sum(lbc.values())
        prep       = prep_map.get(m, 0.0)
        other      = other_map.get(m, 0.0)
        process    = max(total - loss_total - prep - other, 0.0)
        result.append({
            "bulan":            m,
            "total_hour":       total,
            "process_hour":     process,
            "loss_by_category": lbc,
        })
    return result
