"""
Master data controller — CRUD untuk Section, Shift, User,
ProblemCategory, ShopModel, WorkCenter.
"""
import logging

from sqlalchemy import func, text

from database.session import get_session, engine
from models.master import Section, Shift, ProblemGroup, ProblemCategory, ShopModel, WorkCenter
from models.user import User
from models.laporan import DailyReport
from modules.cache import get as _c_get, set as _c_set, invalidate as _c_inv
from controllers.auth_controller import hash_password


# =============================================================================
# SECTION
# =============================================================================

def get_all_sections() -> list:
    cached = _c_get("sections")
    if cached is not None:
        return cached
    with get_session() as session:
        rows = session.query(Section).order_by(Section.name).all()
        result = [(r.id, r.name) for r in rows]
    _c_set("sections", result)
    return result


def tambah_section(nama: str) -> tuple[bool, str]:
    try:
        with get_session() as session:
            exists = session.query(Section).filter(
                func.lower(Section.name) == func.lower(nama)
            ).first()
            if exists:
                return False, f"Shop '{nama}' sudah ada."
            code = nama.strip().upper().replace(" ", "_")
            session.add(Section(code=code, name=nama))
        _c_inv("sections")
        return True, f"Shop '{nama}' berhasil ditambahkan."
    except Exception as e:
        return False, f"Gagal menambah shop: {e}"


def edit_section(section_id: int, nama: str) -> tuple[bool, str]:
    try:
        with get_session() as session:
            dup = session.query(Section).filter(
                func.lower(Section.name) == func.lower(nama),
                Section.id != section_id,
            ).first()
            if dup:
                return False, f"Shop '{nama}' sudah ada."
            sec = session.get(Section, section_id)
            if not sec:
                return False, "Shop tidak ditemukan."
            sec.code = nama.strip().upper().replace(" ", "_")
            sec.name = nama
        _c_inv("sections")
        return True, f"Shop berhasil diubah menjadi '{nama}'."
    except Exception as e:
        return False, f"Gagal mengubah shop: {e}"


def hapus_section(section_id: int) -> tuple[bool, str]:
    try:
        with get_session() as session:
            count = session.query(DailyReport).filter(
                DailyReport.section_id == section_id
            ).count()
            if count > 0:
                return False, f"Shop tidak bisa dihapus — digunakan oleh {count} laporan."
            sec = session.get(Section, section_id)
            if not sec:
                return False, "Shop tidak ditemukan."
            session.delete(sec)
        _c_inv("sections")
        return True, "Shop berhasil dihapus."
    except Exception as e:
        return False, f"Gagal menghapus shop: {e}"


# =============================================================================
# SHIFT
# =============================================================================

def ensure_shift_columns() -> None:
    """Tambah kolom baru ke tabel shift jika belum ada (legacy migration)."""
    with engine.begin() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE shift ADD COLUMN IF NOT EXISTS preparation_min FLOAT DEFAULT 15"
            ))
            conn.execute(text(
                "ALTER TABLE shift ADD COLUMN IF NOT EXISTS other_min FLOAT DEFAULT 10"
            ))
        except Exception:
            pass


def get_all_shifts() -> list:
    cached = _c_get("shifts")
    if cached is not None:
        return cached
    with get_session() as session:
        rows = session.query(Shift).order_by(Shift.id).all()
        result = [r.to_dict() for r in rows]
    _c_set("shifts", result)
    return result


def tambah_shift(
    name: str, start_time: str, end_time: str,
    total_hours: float, preparation_min: float = 15.0, other_min: float = 10.0,
) -> tuple[bool, str]:
    try:
        with get_session() as session:
            exists = session.query(Shift).filter(
                func.lower(Shift.name) == func.lower(name)
            ).first()
            if exists:
                return False, f"Shift '{name}' sudah ada."
            session.add(Shift(
                name=name, start_time=start_time, end_time=end_time,
                total_hours=total_hours, preparation_min=preparation_min, other_min=other_min,
            ))
        _c_inv("shifts")
        return True, f"Shift '{name}' berhasil ditambahkan."
    except Exception as e:
        return False, f"Gagal menambah shift: {e}"


def edit_shift(
    shift_id: int, name: str, start_time: str, end_time: str,
    total_hours: float, preparation_min: float = 15.0, other_min: float = 10.0,
) -> tuple[bool, str]:
    try:
        with get_session() as session:
            dup = session.query(Shift).filter(
                func.lower(Shift.name) == func.lower(name),
                Shift.id != shift_id,
            ).first()
            if dup:
                return False, f"Shift '{name}' sudah ada."
            shift = session.get(Shift, shift_id)
            if not shift:
                return False, "Shift tidak ditemukan."
            shift.name            = name
            shift.start_time      = start_time
            shift.end_time        = end_time
            shift.total_hours     = total_hours
            shift.preparation_min = preparation_min
            shift.other_min       = other_min
        _c_inv("shifts")
        return True, f"Shift berhasil diubah menjadi '{name}'."
    except Exception as e:
        return False, f"Gagal mengubah shift: {e}"


def hapus_shift(shift_id: int) -> tuple[bool, str]:
    try:
        with get_session() as session:
            count = session.query(DailyReport).filter(
                DailyReport.shift_id == shift_id
            ).count()
            if count > 0:
                return False, f"Shift tidak bisa dihapus — digunakan oleh {count} laporan."
            shift = session.get(Shift, shift_id)
            if not shift:
                return False, "Shift tidak ditemukan."
            session.delete(shift)
        _c_inv("shifts")
        return True, "Shift berhasil dihapus."
    except Exception as e:
        return False, f"Gagal menghapus shift: {e}"


def update_shift_working_hour(shift_id: int, working_hour: float) -> tuple[bool, str]:
    try:
        with get_session() as session:
            shift = session.get(Shift, shift_id)
            if not shift:
                return False, "Shift tidak ditemukan."
            shift.total_hours = working_hour
        _c_inv("shifts")
        return True, "Working hour berhasil diperbarui."
    except Exception as e:
        return False, f"Gagal memperbarui working hour: {e}"


# =============================================================================
# USER
# =============================================================================

def get_all_users() -> list:
    cached = _c_get("users")
    if cached is not None:
        return cached
    with get_session() as session:
        rows = session.query(User).order_by(User.name).all()
        result = [r.to_dict() for r in rows]
    _c_set("users", result)
    return result


def tambah_user(nik: str, nama: str, role: str, password_hash: str) -> tuple[bool, str]:
    try:
        with get_session() as session:
            exists = session.query(User).filter(User.nik == nik).first()
            if exists:
                return False, f"NIK '{nik}' sudah terdaftar."
            session.add(User(
                nik=nik, username=nik, name=nama,
                role=role, password_hash=password_hash,
            ))
        _c_inv("users")
        return True, f"User '{nama}' berhasil ditambahkan."
    except Exception as e:
        return False, f"Gagal menambah user: {e}"


def reset_password_user(user_id: int, password_hash: str) -> tuple[bool, str]:
    try:
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return False, "User tidak ditemukan."
            user.password_hash = password_hash
        return True, "Password berhasil direset."
    except Exception as e:
        return False, f"Gagal reset password: {e}"


def hapus_user(user_id: int) -> tuple[bool, str]:
    try:
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return False, "User tidak ditemukan."
            session.delete(user)
        _c_inv("users")
        return True, "User berhasil dihapus."
    except Exception as e:
        return False, f"Gagal menghapus user: {e}"


# =============================================================================
# PROBLEM GROUP & CATEGORY
# =============================================================================

def get_all_groups() -> list:
    cached = _c_get("groups")
    if cached is not None:
        return cached
    with get_session() as session:
        rows = session.query(ProblemGroup).order_by(ProblemGroup.id).all()
        result = [(r.id, r.name) for r in rows]
    _c_set("groups", result)
    return result


def get_all_kategori() -> list:
    cached = _c_get("categories")
    if cached is not None:
        return cached
    with get_session() as session:
        rows = (
            session.query(ProblemCategory)
            .join(ProblemGroup)
            .order_by(ProblemCategory.group_id, ProblemCategory.order_num, ProblemCategory.id)
            .all()
        )
        result = [r.to_dict() for r in rows]
    _c_set("categories", result)
    return result


def get_all_category_names() -> list[str]:
    try:
        with get_session() as session:
            rows = (
                session.query(ProblemCategory)
                .join(ProblemGroup)
                .order_by(ProblemGroup.order_num, ProblemCategory.order_num, ProblemCategory.id)
                .all()
            )
            return [r.name for r in rows]
    except Exception as e:
        logging.error(f"get_all_category_names error: {e}")
        return []


def tambah_kategori(name: str, group_id: int) -> tuple[bool, str]:
    try:
        with get_session() as session:
            exists = session.query(ProblemCategory).filter(
                func.lower(ProblemCategory.name) == func.lower(name)
            ).first()
            if exists:
                return False, f"Kategori '{name}' sudah ada."
            max_order = session.query(func.max(ProblemCategory.order_num)).filter(
                ProblemCategory.group_id == group_id
            ).scalar() or 0
            code = name.strip().upper().replace(" ", "_")
            session.add(ProblemCategory(
                group_id=group_id, code=code, name=name, order_num=max_order + 1
            ))
        _c_inv("categories")
        return True, f"Kategori '{name}' berhasil ditambahkan."
    except Exception as e:
        return False, f"Gagal menambah kategori: {e}"


def edit_kategori(cat_id: int, name: str, group_id: int) -> tuple[bool, str]:
    try:
        with get_session() as session:
            dup = session.query(ProblemCategory).filter(
                func.lower(ProblemCategory.name) == func.lower(name),
                ProblemCategory.id != cat_id,
            ).first()
            if dup:
                return False, f"Kategori '{name}' sudah ada."
            cat = session.get(ProblemCategory, cat_id)
            if not cat:
                return False, "Kategori tidak ditemukan."
            cat.name     = name
            cat.group_id = group_id
        _c_inv("categories")
        return True, f"Kategori berhasil diubah menjadi '{name}'."
    except Exception as e:
        return False, f"Gagal mengubah kategori: {e}"


def hapus_kategori(cat_id: int) -> tuple[bool, str]:
    try:
        with get_session() as session:
            from models.laporan import ProblemRecord
            count = session.query(ProblemRecord).filter(
                ProblemRecord.category_id == cat_id
            ).count()
            if count > 0:
                return False, f"Kategori tidak bisa dihapus — digunakan oleh {count} catatan masalah."
            cat = session.get(ProblemCategory, cat_id)
            if not cat:
                return False, "Kategori tidak ditemukan."
            session.delete(cat)
        _c_inv("categories")
        return True, "Kategori berhasil dihapus."
    except Exception as e:
        return False, f"Gagal menghapus kategori: {e}"


# =============================================================================
# SHOP MODEL
# =============================================================================

def get_models_by_section(section_id: int) -> list:
    with get_session() as session:
        rows = (
            session.query(ShopModel)
            .filter(ShopModel.section_id == section_id)
            .order_by(ShopModel.model_name)
            .all()
        )
        return [r.to_dict() for r in rows]


def tambah_shop_model(
    section_id: int, model_name: str,
    working_hour: float = 0.0, cycle_time: float = 0.0,
) -> tuple[bool, str]:
    try:
        with get_session() as session:
            exists = session.query(ShopModel).filter(
                ShopModel.section_id == section_id,
                func.lower(ShopModel.model_name) == func.lower(model_name),
            ).first()
            if exists:
                return False, f"Model '{model_name}' sudah ada di shop ini."
            session.add(ShopModel(
                section_id=section_id, model_name=model_name,
                working_hour=working_hour, cycle_time=cycle_time,
            ))
        return True, f"Model '{model_name}' berhasil ditambahkan."
    except Exception as e:
        return False, f"Gagal menambah model: {e}"


def edit_shop_model(
    model_id: int, model_name: str,
    working_hour: float, cycle_time: float = 0.0,
) -> tuple[bool, str]:
    try:
        with get_session() as session:
            m = session.get(ShopModel, model_id)
            if not m:
                return False, "Model tidak ditemukan."
            m.model_name   = model_name
            m.working_hour = working_hour
            m.cycle_time   = cycle_time
        return True, f"Model '{model_name}' berhasil diubah."
    except Exception as e:
        return False, f"Gagal mengubah model: {e}"


def hapus_shop_model(model_id: int) -> tuple[bool, str]:
    try:
        with get_session() as session:
            m = session.get(ShopModel, model_id)
            if not m:
                return False, "Model tidak ditemukan."
            session.delete(m)
        return True, "Model berhasil dihapus."
    except Exception as e:
        return False, f"Gagal menghapus model: {e}"


# =============================================================================
# WORK CENTER
# =============================================================================

def get_work_centers_by_section(section_id: int) -> list:
    with get_session() as session:
        rows = (
            session.query(WorkCenter)
            .filter(WorkCenter.section_id == section_id)
            .order_by(WorkCenter.name)
            .all()
        )
        return [r.to_dict() for r in rows]


def tambah_work_center(section_id: int, name: str) -> tuple[bool, str]:
    try:
        with get_session() as session:
            exists = session.query(WorkCenter).filter(
                WorkCenter.section_id == section_id,
                func.lower(WorkCenter.name) == func.lower(name),
            ).first()
            if exists:
                return False, f"Work Center '{name}' sudah ada di shop ini."
            session.add(WorkCenter(section_id=section_id, name=name))
        return True, f"Work Center '{name}' berhasil ditambahkan."
    except Exception as e:
        return False, f"Gagal menambah work center: {e}"


def edit_work_center(wc_id: int, name: str) -> tuple[bool, str]:
    try:
        with get_session() as session:
            wc = session.get(WorkCenter, wc_id)
            if not wc:
                return False, "Work Center tidak ditemukan."
            wc.name = name
        return True, f"Work Center berhasil diubah menjadi '{name}'."
    except Exception as e:
        return False, f"Gagal mengubah work center: {e}"


def hapus_work_center(wc_id: int) -> tuple[bool, str]:
    try:
        with get_session() as session:
            wc = session.get(WorkCenter, wc_id)
            if not wc:
                return False, "Work Center tidak ditemukan."
            session.delete(wc)
        return True, "Work Center berhasil dihapus."
    except Exception as e:
        return False, f"Gagal menghapus work center: {e}"
