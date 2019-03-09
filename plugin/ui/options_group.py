from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAbstractButton, QGroupBox

from .qt.options_qt5 import Ui_OptionsGroup


class OptionsGroup(QGroupBox, Ui_OptionsGroup):

    on_zoom_change = pyqtSignal()

    _TILE_LIMIT_ENABLED = "tile_limit_enabled"
    _TILE_LIMIT = "tile_limit"
    _MERGE_TILES = "merge_tiles"
    _CLIP_TILES = "clip_tiles"
    _AUTO_ZOOM = "auto_zoom"
    _MAX_ZOOM = "max_zoom"
    _FIX_ZOOM_ENABLED = "fix_zoom_enabled"
    _FIX_ZOOM = "fix_zoom"
    _APPLY_STYLES = "apply_styles"
    _SET_BACKGROUND_COLOR = "set_background_color"
    _MODE = "mode"
    _IGNORE_CRS = "ignore_crs"

    class Mode(object):
        MANUAL = "manual"
        BASE_MAP = "base_map"
        INSPECTION = "inspection"
        ANALYSIS = "analysis"

    _options = {
        _TILE_LIMIT_ENABLED: True,
        _TILE_LIMIT: 32,
        _MERGE_TILES: False,
        _CLIP_TILES: False,
        _AUTO_ZOOM: True,
        _MAX_ZOOM: False,
        _FIX_ZOOM: 0,
        _FIX_ZOOM_ENABLED: False,
        _APPLY_STYLES: True,
        _SET_BACKGROUND_COLOR: True,
        _MODE: Mode.MANUAL,
        _IGNORE_CRS: False,
    }

    def __init__(self, settings, target_groupbox, zoom_change_handler):
        super(QGroupBox, self).__init__()
        self.setupUi(target_groupbox)
        self.settings = None
        self._reset_to_basemap_defaults()
        self.settings = settings
        self._zoom_change_handler = zoom_change_handler
        self.lblZoomRange.setText("")
        self.chkLimitNrOfTiles.toggled.connect(lambda enabled: self.spinNrOfLoadedTiles.setEnabled(enabled))
        self.chkMergeTiles.toggled.connect(lambda enabled: self._set_option(self._MERGE_TILES, enabled))
        self.chkClipTiles.toggled.connect(lambda enabled: self._set_option(self._CLIP_TILES, enabled))
        self.chkIgnoreCrsFromMetadata.toggled.connect(lambda enabled: self._set_option(self._IGNORE_CRS, enabled))
        self.chkSetBackgroundColor.toggled.connect(self._on_bg_color_change)
        self.chkApplyStyles.toggled.connect(self._on_apply_styles_changed)
        self.chkLimitNrOfTiles.toggled.connect(lambda enabled: self._set_option(self._TILE_LIMIT_ENABLED, enabled))
        self.rbZoomManual.toggled.connect(self._on_manual_zoom_enabled)
        self.rbZoomMax.toggled.connect(self._on_max_zoom_selected)
        self.chkAutoZoom.toggled.connect(self._on_auto_zoom_enabled)
        self.btnResetToBasemapDefaults.clicked.connect(self._reset_to_basemap_defaults)
        self.btnResetToInspectionDefaults.clicked.connect(self._reset_to_inspection_defaults)
        self.btnResetToAnalysisDefaults.clicked.connect(self._reset_to_analysis_defaults)
        self.btnManualSettings.clicked.connect(lambda: self._enable_manual_mode(True))
        self._load_options()
        self.spinNrOfLoadedTiles.valueChanged.connect(lambda v: self._set_option(self._TILE_LIMIT, v))
        self.zoomSpin.valueChanged.connect(self._on_manual_zoom_change)
        self._current_zoom = None

    def _on_bg_color_change(self, enabled: bool) -> None:
        self._set_option(self._SET_BACKGROUND_COLOR, enabled)
        if enabled and not self.chkApplyStyles.isChecked():
            self.chkApplyStyles.setChecked(True)

    def set_checked(self, target: QAbstractButton, key: str) -> None:
        checked = self._options[key] in (True, "true", "True")
        target.setChecked(checked)

    def _load_options(self) -> None:
        opt = self._options
        for key in self._options:
            self._options[key] = self.settings.value("options/{}".format(key), None)
        if opt[self._TILE_LIMIT_ENABLED]:
            self.set_checked(self.chkLimitNrOfTiles, self._TILE_LIMIT_ENABLED)
        if opt[self._TILE_LIMIT]:
            self.spinNrOfLoadedTiles.setValue(int(opt[self._TILE_LIMIT]))
        if opt[self._MERGE_TILES]:
            self.set_checked(self.chkMergeTiles, self._MERGE_TILES)
        if opt[self._CLIP_TILES]:
            self.set_checked(self.chkClipTiles, self._CLIP_TILES)
        if opt[self._AUTO_ZOOM]:
            self.set_checked(self.chkAutoZoom, self._AUTO_ZOOM)
        if opt[self._MAX_ZOOM]:
            self.set_checked(self.rbZoomMax, self._MAX_ZOOM)
        if opt[self._FIX_ZOOM]:
            self.zoomSpin.setValue(int(opt[self._FIX_ZOOM]))
        if opt[self._FIX_ZOOM_ENABLED]:
            self.set_checked(self.rbZoomManual, self._FIX_ZOOM_ENABLED)
        if opt[self._APPLY_STYLES]:
            self.set_checked(self.chkApplyStyles, self._APPLY_STYLES)
        if opt[self._SET_BACKGROUND_COLOR]:
            self.set_checked(self.chkSetBackgroundColor, self._SET_BACKGROUND_COLOR)
        if opt[self._IGNORE_CRS]:
            self.set_checked(self.chkIgnoreCrsFromMetadata, self._IGNORE_CRS)
        if opt[self._MODE]:
            val = opt[self._MODE]
            self._enable_manual_mode(val == self.Mode.MANUAL)
            self.btnManualSettings.setChecked(val == self.Mode.MANUAL)
            self.btnResetToInspectionDefaults.setChecked(val == self.Mode.INSPECTION)
            self.btnResetToBasemapDefaults.setChecked(val == self.Mode.BASE_MAP)
            self.btnResetToAnalysisDefaults.setChecked(val == self.Mode.ANALYSIS)
        else:
            self.btnManualSettings.setChecked(True)

    def _on_apply_styles_changed(self, enabled):
        self._set_option(self._APPLY_STYLES, enabled)
        self.chkSetBackgroundColor.setChecked(enabled)

    def _set_option(self, key, value):
        self._options[key] = value
        self.settings.setValue("options/{}".format(key), value)

    def _on_auto_zoom_enabled(self, enabled):
        self._set_option(self._AUTO_ZOOM, enabled)
        self.rbZoomManual.setEnabled(not enabled)
        self.rbZoomMax.setEnabled(not enabled)
        self.zoomSpin.setEnabled(not enabled)
        self._zoom_change_handler()

    def _on_manual_zoom_enabled(self, enabled):
        self._set_option(self._FIX_ZOOM_ENABLED, enabled)
        self._on_manual_zoom_change()

    def _on_manual_zoom_change(self):
        zoom = self.zoomSpin.value()
        self._set_option(self._FIX_ZOOM, zoom)
        self._zoom_change_handler()

    def _on_max_zoom_selected(self, enabled):
        self._set_option(self._MAX_ZOOM, enabled)
        self._zoom_change_handler()

    def ignore_crs_from_metadata(self):
        return self.chkIgnoreCrsFromMetadata.isChecked()

    def is_manual_mode(self):
        return self.btnManualSettings.isChecked()

    def set_zoom_level(self, zoom_level, set_immediately=True):
        if set_immediately:
            self.zoomSpin.setValue(zoom_level)
        else:
            self._current_zoom = zoom_level

    def set_nr_of_tiles(self, nr_tiles):
        self.lblNumberTilesInCurrentExtent.setText("(Current extent: {} tiles)".format(nr_tiles))

    def _reset_to_basemap_defaults(self):
        self._set_settings(
            auto_zoom=True,
            fix_zoom=False,
            tile_limit=32,
            styles_enabled=True,
            merging_enabled=False,
            clip_tile_at_bounds=False,
            background_color=True,
        )
        if self.settings:
            self._set_option("mode", self.Mode.BASE_MAP)
        self._enable_manual_mode(False)

    def _reset_to_analysis_defaults(self):
        self._set_settings(
            auto_zoom=False,
            fix_zoom=True,
            tile_limit=10,
            styles_enabled=False,
            merging_enabled=True,
            clip_tile_at_bounds=True,
            background_color=False,
        )
        if self._current_zoom:
            self.set_zoom_level(self._current_zoom)
        self._set_option("mode", self.Mode.ANALYSIS)
        self._enable_manual_mode(False)

    def _reset_to_inspection_defaults(self):
        self._set_settings(
            auto_zoom=False,
            fix_zoom=False,
            tile_limit=1,
            styles_enabled=False,
            merging_enabled=False,
            clip_tile_at_bounds=False,
            background_color=False,
        )
        self._set_option("mode", self.Mode.INSPECTION)
        self._enable_manual_mode(False)

    def _enable_manual_mode(self, enabled):
        if enabled:
            self._set_option("mode", self.Mode.MANUAL)
        self.chkLimitNrOfTiles.setEnabled(enabled)
        self.spinNrOfLoadedTiles.setEnabled(enabled)
        self.chkMergeTiles.setEnabled(enabled)
        self.chkClipTiles.setEnabled(enabled)
        self.chkAutoZoom.setEnabled(enabled)
        self.rbZoomMax.setEnabled(enabled and not self.chkAutoZoom.isChecked())
        self.rbZoomManual.setEnabled(enabled and not self.chkAutoZoom.isChecked())
        self.zoomSpin.setEnabled(enabled and not self.chkAutoZoom.isChecked())
        self.chkApplyStyles.setEnabled(enabled)
        self.chkSetBackgroundColor.setEnabled(enabled)

    def _set_settings(
        self, auto_zoom, fix_zoom, tile_limit, styles_enabled, merging_enabled, clip_tile_at_bounds, background_color
    ):
        self.rbZoomMax.setChecked(not auto_zoom and not fix_zoom)
        self.chkAutoZoom.setChecked(auto_zoom)
        self.rbZoomManual.setChecked(fix_zoom)
        tile_limit_enabled = tile_limit is not None
        self.chkLimitNrOfTiles.setChecked(tile_limit_enabled)
        if tile_limit_enabled:
            self.spinNrOfLoadedTiles.setValue(tile_limit)
        self.chkApplyStyles.setChecked(styles_enabled)
        self.chkMergeTiles.setChecked(merging_enabled)
        self.chkClipTiles.setChecked(clip_tile_at_bounds)
        self.chkSetBackgroundColor.setChecked(background_color)

    def set_styles_enabled(self, enabled):
        self._set_option(self._APPLY_STYLES, enabled)
        self.chkApplyStyles.setChecked(enabled)

    def is_inspection_mode(self):
        return self.btnResetToInspectionDefaults.isChecked()

    def set_zoom(self, min_zoom=None, max_zoom=None):
        if min_zoom is not None:
            self.zoomSpin.setMinimum(min_zoom)
        else:
            self.zoomSpin.setMinimum(0)
        max_zoom_text = "Max. Zoom"
        if max_zoom is not None:
            self.zoomSpin.setMaximum(max_zoom)
            max_zoom_text += " ({})".format(max_zoom)
        else:
            self.zoomSpin.setMaximum(23)
        self.rbZoomMax.setText(max_zoom_text)

        zoom_range_text = ""
        if min_zoom is not None or max_zoom is not None:
            zoom_range_text = "({} - {})".format(min_zoom, max_zoom)
        self.lblZoomRange.setText(zoom_range_text)

    def clip_tiles(self):
        enabled = self.chkClipTiles.isChecked()
        self._set_option(self._CLIP_TILES, enabled)
        return enabled

    def auto_zoom_enabled(self):
        enabled = self.chkAutoZoom.isChecked()
        self._set_option(self._AUTO_ZOOM, enabled)
        return enabled

    def manual_zoom(self):
        enabled = self.rbZoomManual.isChecked() and not self.chkAutoZoom.isChecked()
        fix_zoom = self.zoomSpin.value()
        self._set_option(self._FIX_ZOOM_ENABLED, enabled)
        self._set_option(self._FIX_ZOOM, fix_zoom)
        if not enabled:
            return None
        return fix_zoom

    def tile_number_limit(self):
        enabled = self.chkLimitNrOfTiles.isChecked()
        tile_limit = self.spinNrOfLoadedTiles.value()
        self._set_option(self._TILE_LIMIT_ENABLED, enabled)
        self._set_option(self._TILE_LIMIT, tile_limit)
        if not enabled:
            return None
        return tile_limit

    def apply_styles_enabled(self):
        enabled = self.chkApplyStyles.isChecked()
        self._set_option(self._APPLY_STYLES, enabled)
        return enabled

    def set_background_color_enabled(self):
        enabled = self.chkSetBackgroundColor.isChecked()
        self._set_option(self._SET_BACKGROUND_COLOR, enabled)
        return enabled

    def merge_tiles_enabled(self):
        enabled = self.chkMergeTiles.isChecked()
        self._set_option(self._MERGE_TILES, enabled)
        return enabled
