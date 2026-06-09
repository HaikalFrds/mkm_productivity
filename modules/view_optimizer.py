"""
View optimizer — LazyViewMixin.

Gunakan sebagai mixin di QWidget subclass:

    class MyWidget(LazyViewMixin, QWidget):
        def _on_first_show(self):
            # dipanggil SEKALI: load sections, shifts, dll
            ...
        def _on_show(self):
            # dipanggil setiap show berikutnya (opsional)
            ...

API:
  widget.refresh()  → paksa _on_first_show jalan lagi saat show berikutnya
"""


class LazyViewMixin:
    """
    Mixin untuk QWidget: pisahkan inisialisasi data (sekali) dari refresh ringan
    (setiap tampil).  Menghemat rebuild UI yang tidak perlu setiap klik sidebar.
    """

    _view_ready: bool = False

    # ── Qt hook ───────────────────────────────────────────────────────────────

    def showEvent(self, event):           # noqa: N802
        super().showEvent(event)          # type: ignore[misc]
        if not self._view_ready:
            self._view_ready = True
            self._on_first_show()
        else:
            self._on_show()

    # ── Override di subclass ──────────────────────────────────────────────────

    def _on_first_show(self) -> None:
        """Dipanggil SEKALI saat widget pertama kali ditampilkan."""

    def _on_show(self) -> None:
        """Dipanggil setiap kali widget ditampilkan (setelah first show)."""

    # ── Utility ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Paksa _on_first_show dijalankan ulang saat show berikutnya."""
        self._view_ready = False
