"""
Dashboard controller — agregasi data untuk halaman dashboard & chart bulanan.
"""
import logging
from datetime import date as _date
from sqlalchemy import text
from database.session import get_session


def get_dashboard_data() -> dict:
    today = _date.today()
    try:
        with get_session() as session:
            r = session.execute(text("""
                SELECT COUNT(DISTINCT dr.id), COALESCE(SUM(pr.loss_time), 0)
                FROM daily_report dr
                LEFT JOIN problem_record pr ON pr.report_id = dr.id
                WHERE dr.date = :today
            """), {"today": today}).fetchone()
            report_count = int(r[0]) if r else 0
            loss_today   = float(r[1]) if r else 0.0

            cat_rows = session.execute(text("""
                SELECT pg.name, pg.order_num, COALESCE(SUM(pr.loss_time), 0)
                FROM problem_record pr
                JOIN daily_report dr ON dr.id = pr.report_id
                JOIN problem_category pc ON pc.id = pr.category_id
                JOIN problem_group pg ON pg.id = pc.group_id
                WHERE EXTRACT(MONTH FROM dr.date) = :m
                  AND EXTRACT(YEAR  FROM dr.date) = :y
                GROUP BY pg.name, pg.order_num
                ORDER BY pg.order_num
            """), {"m": today.month, "y": today.year}).fetchall()
            categories = [{"group": r[0], "hours": float(r[2])} for r in cat_rows]

            recent_rows = session.execute(text("""
                SELECT dr.date, s.name, COALESCE(SUM(pr.loss_time), 0), dr.status
                FROM daily_report dr
                JOIN section s ON s.id = dr.section_id
                LEFT JOIN problem_record pr ON pr.report_id = dr.id
                GROUP BY dr.id, dr.date, s.name, dr.status
                ORDER BY dr.date DESC, dr.id DESC
                LIMIT 5
            """)).fetchall()
            recent = [{"date": r[0], "shop": r[1], "loss": float(r[2]), "status": r[3]}
                      for r in recent_rows]

            r2 = session.execute(text("""
                SELECT COALESCE(SUM(s.total_hours), 0),
                       COALESCE(SUM(s.preparation_min / 60.0), 0),
                       COALESCE(SUM(s.other_min / 60.0), 0)
                FROM daily_report dr
                JOIN shift s ON s.id = dr.shift_id
                WHERE EXTRACT(MONTH FROM dr.date) = :m
                  AND EXTRACT(YEAR  FROM dr.date) = :y
            """), {"m": today.month, "y": today.year}).fetchone()
            total_h = float(r2[0] or 0)
            prep_h  = float(r2[1] or 0)
            other_h = float(r2[2] or 0)

            r3 = session.execute(text("""
                SELECT COALESCE(SUM(
                    CASE WHEN dp.ot_2h  THEN 2.0  ELSE 0 END +
                    CASE WHEN dp.ot_3h  THEN 3.0  ELSE 0 END +
                    CASE WHEN dp.ot_11h THEN 11.0 ELSE 0 END
                ), 0)
                FROM (SELECT DISTINCT ON (report_id) report_id, ot_2h, ot_3h, ot_11h
                      FROM daily_production) dp
                JOIN daily_report dr ON dr.id = dp.report_id
                WHERE EXTRACT(MONTH FROM dr.date) = :m
                  AND EXTRACT(YEAR  FROM dr.date) = :y
            """), {"m": today.month, "y": today.year}).fetchone()
            total_h += float((r3 or [0])[0] or 0)

            r4 = session.execute(text("""
                SELECT COALESCE(SUM(pr.loss_time), 0)
                FROM problem_record pr
                JOIN daily_report dr ON dr.id = pr.report_id
                WHERE EXTRACT(MONTH FROM dr.date) = :m
                  AND EXTRACT(YEAR  FROM dr.date) = :y
            """), {"m": today.month, "y": today.year}).fetchone()
            loss_bln = float((r4 or [0])[0] or 0)

        process_h = max(total_h - loss_bln - prep_h - other_h, 0.0)
        ratio     = (process_h / total_h * 100) if total_h > 0 else 0.0

        return {
            "report_count":  report_count,
            "loss_today":    loss_today,
            "categories":    categories,
            "recent":        recent,
            "process_ratio": ratio,
        }
    except Exception as e:
        logging.error(f"get_dashboard_data error: {e}")
        return {"report_count": 0, "loss_today": 0.0, "categories": [], "recent": [], "process_ratio": None}


def get_monthly_loss_by_group(year: int) -> list:
    with get_session() as session:
        shift_rows = session.execute(text("""
            SELECT EXTRACT(MONTH FROM dr.date)::int,
                   COALESCE(SUM(s.total_hours), 0),
                   COALESCE(SUM(s.preparation_min / 60.0), 0),
                   COALESCE(SUM(s.other_min / 60.0), 0)
            FROM daily_report dr
            JOIN shift s ON s.id = dr.shift_id
            WHERE EXTRACT(YEAR FROM dr.date) = :y
            GROUP BY 1
        """), {"y": year}).fetchall()
        shift_hours = {}
        prep_map    = {}
        other_map   = {}
        for r in shift_rows:
            shift_hours[r[0]] = float(r[1])
            prep_map[r[0]]    = float(r[2])
            other_map[r[0]]   = float(r[3])

        loss_rows = session.execute(text("""
            SELECT EXTRACT(MONTH FROM dr.date)::int,
                   pg.name, pg.order_num, COALESCE(SUM(pr.loss_time), 0)
            FROM problem_record pr
            JOIN daily_report dr ON dr.id = pr.report_id
            JOIN problem_category pc ON pc.id = pr.category_id
            JOIN problem_group pg ON pg.id = pc.group_id
            WHERE EXTRACT(YEAR FROM dr.date) = :y
            GROUP BY 1, 2, 3 ORDER BY 1, 3
        """), {"y": year}).fetchall()
        loss_map: dict = {}
        for bulan, gname, _, val in loss_rows:
            loss_map.setdefault(bulan, {})[gname] = float(val)

        ot_rows = session.execute(text("""
            SELECT EXTRACT(MONTH FROM dr.date)::int,
                   COALESCE(SUM(
                       CASE WHEN dp.ot_2h  THEN 2.0  ELSE 0 END +
                       CASE WHEN dp.ot_3h  THEN 3.0  ELSE 0 END +
                       CASE WHEN dp.ot_11h THEN 11.0 ELSE 0 END
                   ), 0)
            FROM (SELECT DISTINCT ON (report_id) report_id, ot_2h, ot_3h, ot_11h
                  FROM daily_production) dp
            JOIN daily_report dr ON dr.id = dp.report_id
            WHERE EXTRACT(YEAR FROM dr.date) = :y
            GROUP BY 1
        """), {"y": year}).fetchall()
        ot_map = {r[0]: float(r[1]) for r in ot_rows}

    result = []
    for m in range(1, 13):
        total      = shift_hours.get(m, 0.0) + ot_map.get(m, 0.0)
        by_group   = loss_map.get(m, {})
        loss_total = sum(by_group.values())
        prep       = prep_map.get(m, 0.0)
        other      = other_map.get(m, 0.0)
        process    = max(total - loss_total - prep - other, 0.0)
        pct        = round(process / total * 100, 1) if total > 0 else 0.0
        result.append({
            "bulan":       m,
            "total_hour":  total,
            "loss_total":  loss_total,
            "process_pct": pct,
            "by_group":    by_group,
        })
    return result
