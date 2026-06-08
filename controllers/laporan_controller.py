"""
Laporan controller — simpan, hapus, dan baca detail laporan harian.
"""
import logging

from sqlalchemy import text

from database.session import get_session
from models.laporan import (
    DailyReport, DailyProduction, ProblemRecord,
    Manpower, Absen, InhouseClaim, MaterialUsage,
)
from models.master import Section, Shift, ProblemCategory


def simpan_laporan_harian(
    user_id: int,
    header: dict,
    catatan: list,
    produksi: list,
    inhouse_claim: list = None,
    manpower: list = None,
    absen: list = None,
    material_usage: list = None,
) -> tuple[bool, str]:
    try:
        with get_session() as session:
            # 1. Resolusi shift_id
            shift = session.query(Shift).filter(
                Shift.name == header["shift"]
            ).first()
            if not shift:
                return False, f"Shift '{header['shift']}' tidak ditemukan di database"

            # 2. Resolusi section_id
            section = session.query(Section).filter(
                Section.name == header["section"]
            ).first()
            if not section:
                return False, f"Shop '{header['section']}' tidak ditemukan di database"

            # 3. Insert daily_report
            report = DailyReport(
                user_id=user_id,
                shift_id=shift.id,
                section_id=section.id,
                date=header["tanggal"],
                coordinator=header["koordinator"],
                approved_by=header["approved_by"],
                checked_by=header["checked_by"],
                status="draft",
            )
            session.add(report)
            session.flush()  # dapat report.id tanpa commit

            # 4. Produksi
            for p in produksi:
                if not p.get("model"):
                    continue
                session.add(DailyProduction(
                    report_id=report.id,
                    model=p["model"],
                    plan_unit=p.get("plan_unit")    or 0,
                    actual_unit=p.get("actual_unit") or 0,
                    plan_whour=p.get("plan_whour")   or 0,
                    actual_whour=p.get("actual_whour") or 0,
                    ot_2h=bool(p.get("ot_2h",  False)),
                    ot_3h=bool(p.get("ot_3h",  False)),
                    ot_11h=bool(p.get("ot_11h", False)),
                ))

            # 5. Catatan masalah
            for c in catatan:
                if not c.get("deskripsi"):
                    continue
                cat = session.query(ProblemCategory).filter(
                    ProblemCategory.name == c["kategori"]
                ).first()
                session.add(ProblemRecord(
                    report_id=report.id,
                    category_id=cat.id if cat else None,
                    ra_number=c.get("nomor_ra")  or None,
                    description=c.get("deskripsi") or None,
                    cause=c.get("penyebab")  or None,
                    corrective_action=c.get("tindakan") or None,
                    pic=c.get("pic")       or None,
                    start_time=c.get("start_time") or None,
                    end_time=c.get("end_time")   or None,
                    down_time=c.get("down_time") or 0.0,
                    loss_time=c.get("loss_time") or 0.0,
                    date=header["tanggal"],
                ))

            # 6. Inhouse claim
            for ic in (inhouse_claim or []):
                session.add(InhouseClaim(
                    report_id=report.id,
                    tanggal=ic.get("tanggal")  or None,
                    model=ic.get("model")     or None,
                    op_no_st=ic.get("op_no_st")  or None,
                    item=ic.get("item")      or None,
                    qty=ic.get("qty")       or 0,
                    satuan=ic.get("satuan")    or None,
                    penyebab=ic.get("penyebab")  or None,
                    tindakan=ic.get("tindakan")  or None,
                    faktor=ic.get("faktor")    or None,
                    stop_hr=ic.get("stop_hr")   or 0,
                    lost_hr=ic.get("lost_hr")   or 0,
                    status=ic.get("status")    or None,
                ))

            # 7. Manpower
            for mp in (manpower or []):
                session.add(Manpower(
                    report_id=report.id,
                    role=mp.get("role") or None,
                    plan_count=mp.get("plan") or 0,
                    act_count=mp.get("act")  or 0,
                ))

            # 8. Absen
            for ab in (absen or []):
                session.add(Absen(
                    report_id=report.id,
                    no=ab.get("no"),
                    nama=ab.get("nama")        or None,
                    nik=ab.get("nik")         or None,
                    shop=ab.get("shop")        or None,
                    keterangan=ab.get("keterangan")  or None,
                ))

            # 9. Material usage
            for mat in (material_usage or []):
                if not mat.get("material_name"):
                    continue
                session.add(MaterialUsage(
                    report_id=report.id,
                    material_name=mat.get("material_name") or None,
                    material_no=mat.get("material_no")   or None,
                    qty=mat.get("qty")            or 0,
                    satuan=mat.get("satuan")         or None,
                    keterangan=mat.get("keterangan")     or None,
                ))

            saved_id = report.id  # simpan sebelum session close

        return True, f"Laporan berhasil disimpan! (ID: {saved_id})"

    except Exception as e:
        return False, f"Gagal menyimpan laporan: {str(e)}"


def hapus_laporan(report_id: int) -> tuple[bool, str]:
    try:
        with get_session() as session:
            report = session.get(DailyReport, report_id)
            if not report:
                return False, f"Laporan #{report_id} tidak ditemukan."
            session.delete(report)  # cascade delete semua child rows
        return True, f"Laporan #{report_id} berhasil dihapus."
    except Exception as e:
        return False, f"Gagal menghapus laporan: {e}"


def get_detail_laporan(report_id: int) -> tuple:
    """
    Return (header, produksi, catatan, manpower, absen, inhouse_claim, materials).
    Pakai text() query untuk fleksibilitas JOIN yang kompleks.
    """
    with get_session() as session:
        row = session.execute(text("""
            SELECT dr.id, dr.date, sec.name, sh.name,
                   dr.coordinator, dr.approved_by, dr.checked_by, s.total_hours
            FROM daily_report dr
            JOIN section sec ON sec.id = dr.section_id
            JOIN shift   sh  ON sh.id  = dr.shift_id
            JOIN shift   s   ON s.id   = dr.shift_id
            WHERE dr.id = :id
        """), {"id": report_id}).fetchone()

        if not row:
            return None, [], [], [], [], [], []

        # Overtime
        ot_row = session.execute(text("""
            SELECT ot_2h, ot_3h, ot_11h FROM daily_production
            WHERE report_id = :id LIMIT 1
        """), {"id": report_id}).fetchone()

        overtime_text = "-"
        if ot_row:
            if ot_row[0]:   overtime_text = "2H"
            elif ot_row[1]: overtime_text = "3H"
            elif ot_row[2]: overtime_text = "11.4H"

        header = {
            "id": row[0], "date": str(row[1]), "section": row[2],
            "shift": row[3], "coordinator": row[4],
            "approved_by": row[5], "checked_by": row[6],
            "shift_duration": float(row[7]) if row[7] is not None else 0.0,
            "overtime": overtime_text,
        }

        produksi_rows = session.execute(text("""
            SELECT model, plan_unit, actual_unit, plan_whour, actual_whour,
                   ot_2h, ot_3h, ot_11h
            FROM daily_production WHERE report_id = :id ORDER BY id
        """), {"id": report_id}).fetchall()
        produksi = [
            {
                "model":        r[0],
                "plan_unit":    float(r[1] or 0),
                "actual_unit":  float(r[2] or 0),
                "plan_whour":   float(r[3] or 0),
                "actual_whour": float(r[4] or 0),
                "ot_2h":        bool(r[5]),
                "ot_3h":        bool(r[6]),
                "ot_11h":       bool(r[7]),
            }
            for r in produksi_rows
        ]

        catatan_rows = session.execute(text("""
            SELECT pr.ra_number, pc.name, pr.description, pr.cause,
                   pr.corrective_action, pr.pic,
                   pr.start_time, pr.end_time, pr.down_time, pr.loss_time
            FROM problem_record pr
            LEFT JOIN problem_category pc ON pc.id = pr.category_id
            WHERE pr.report_id = :id ORDER BY pr.id
        """), {"id": report_id}).fetchall()
        catatan = [
            {
                "ra_number":        r[0] or "", "category": r[1] or "",
                "description":      r[2] or "", "cause":    r[3] or "",
                "corrective_action": r[4] or "", "pic":     r[5] or "",
                "start_time":  str(r[6]) if r[6] else "",
                "end_time":    str(r[7]) if r[7] else "",
                "down_time":   float(r[8] or 0),
                "loss_time":   float(r[9] or 0),
            }
            for r in catatan_rows
        ]

        manpower_rows = session.execute(text("""
            SELECT role, plan_count, act_count FROM manpower
            WHERE report_id = :id ORDER BY id
        """), {"id": report_id}).fetchall()
        manpower = [
            {"role": r[0] or "", "plan": int(r[1] or 0), "act": int(r[2] or 0)}
            for r in manpower_rows
        ]

        absen_rows = session.execute(text("""
            SELECT no, nama, nik, shop, keterangan FROM absen
            WHERE report_id = :id ORDER BY no
        """), {"id": report_id}).fetchall()
        absen = [
            {"no": r[0], "nama": r[1] or "", "nik": r[2] or "",
             "shop": r[3] or "", "keterangan": r[4] or ""}
            for r in absen_rows
        ]

        inhouse_rows = session.execute(text("""
            SELECT model, op_no_st, item, qty, satuan,
                   penyebab, tindakan, faktor, stop_hr, lost_hr, status
            FROM inhouse_claim WHERE report_id = :id ORDER BY id
        """), {"id": report_id}).fetchall()
        inhouse_claim = [
            {
                "model": r[0] or "", "op_no_st": r[1] or "", "item": r[2] or "",
                "qty":      float(r[3] or 0),
                "satuan":   r[4] or "", "penyebab": r[5] or "",
                "tindakan": r[6] or "", "faktor":   r[7] or "",
                "stop_hr":  float(r[8]  or 0),
                "lost_hr":  float(r[9]  or 0),
                "status":   r[10] or "",
            }
            for r in inhouse_rows
        ]

        material_rows = session.execute(text("""
            SELECT material_name, material_no, qty, satuan, keterangan
            FROM material_usage WHERE report_id = :id ORDER BY id
        """), {"id": report_id}).fetchall()
        materials = [
            {
                "material_name": r[0] or "", "material_no": r[1] or "",
                "qty": float(r[2] or 0), "satuan": r[3] or "",
                "keterangan": r[4] or "",
            }
            for r in material_rows
        ]

    return header, produksi, catatan, manpower, absen, inhouse_claim, materials
