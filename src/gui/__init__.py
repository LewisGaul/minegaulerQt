"""
This file contains the GUI for minesweeper in two parts: the layout (BasicGui)
and the view and controller part of the app (GameGui).
"""

import sys
from os.path import join, exists, basename, dirname
from glob import glob
import time as tm
import logging
import json

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from .. import pkg_direc, img_direc
from ..utils import get_nbrs, blend_colours
from .highscores import (
    HighscoresWindow, get_hscore_position, enchs, include_old_hscores,
    save_all_highscores, LooseVersion
    )


def QMouseButton_to_int(QMouseButton):
    if QMouseButton == Qt.LeftButton:
        return int(Qt.LeftButton)
    elif QMouseButton == Qt.RightButton:
        return int(Qt.RightButton)
    elif QMouseButton == Qt.LeftButton | Qt.RightButton:
        return int(Qt.LeftButton | Qt.RightButton)


class GameGUI(QMainWindow):
    def __init__(self, processor):
        global app
        app = QApplication(sys.argv)
        super().__init__()
        self.setWindowTitle('MineGaulerQt')
        self.procr = processor
        for s in ['btn_size', 'styles']:
            setattr(self, s, getattr(self.procr, s))
        self.icon = QIcon(join(img_direc, 'icon.ico'))
        self.setWindowIcon(self.icon)
        # Disable maximise button
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        # Create highscores window
        self.hscores_window = HighscoresWindow(self)
        self.hscores_window.setWindowIcon(self.icon)
        self.setupUI()
        self.open_windows = {'main': self}
        self.state = 'ready'
    def setupUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        vlayout = QVBoxLayout(central_widget)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        # Top panel widget configuration
        self.panel_frame = QFrame(central_widget)
        self.panel_frame.setFixedHeight(40)
        self.panel_frame.setFrameShadow(QFrame.Sunken)
        self.panel_frame.setFrameShape(QFrame.Panel)
        self.panel_frame.setLineWidth(2)
        self.panel = TopPanel(self.panel_frame, self)
        vlayout.addWidget(self.panel_frame)
        lyt = QVBoxLayout(self.panel_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(self.panel)
        # Main body widget config - use horizontal layout for centre alignment
        hstretch = QHBoxLayout()
        hstretch.addStretch() #left-padding for centering
        self.body = QFrame(central_widget) #minefield frame
        self.body.setFrameShadow(QFrame.Raised)
        self.body.setFrameShape(QFrame.Box)
        self.body.setLineWidth(5)
        hstretch.addWidget(self.body)
        hstretch.addStretch() #right-padding for centering
        vlayout.addLayout(hstretch)
        lyt = QVBoxLayout(self.body)
        self.mf_widget = MinefieldWidget(self.body, self.procr, self)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(self.mf_widget)
        self.make_menubar()
        # Name entry bar underneath the minefield
        self.namebar = NameBar(central_widget, self)
        # self.namebar.mouseDoubleClickEvent = lambda e=None: self.namebar.setEnabled
        vlayout.addWidget(self.namebar)
    def make_menubar(self):
        menu = self.menubar = self.menuBar() #QMainWindow has QMenuBar already
        game_menu = menu.addMenu('Game')
        opts_menu = menu.addMenu('Options')
        help_menu = menu.addMenu('Help')
        # GAME MENU
        # New game action
        new_act = QAction('New', self)
        new_act.triggered.connect(self.procr.prepare_new_game)
        new_act.setShortcut('F2')
        game_menu.addAction(new_act)
        # Replay game action
        # replay_act = QAction('Replay', self)
        # replay_act.triggered.connect(SOMETHING)
        # replay_act.setShortcut('F3')
        # game_menu.addAction(replay_act)
        # Show highscores action
        hs_act = QAction('Highscores', self)
        hs_act.triggered.connect(self.show_highscores)
        hs_act.setShortcut('F6')
        game_menu.addAction(hs_act)
        game_menu.addSeparator() #new section
        # Show probabilities action
        prob_act = QAction('Show probabilities', self)
        prob_act.triggered.connect(self.show_probs)
        prob_act.setShortcut('F5')
        game_menu.addAction(prob_act)
        game_menu.addSeparator() #new section
        # Difficulty radiobuttons
        self.diff_group = QActionGroup(self, exclusive=True)
        for diff in ['Beginner', 'Intermediate', 'Expert', 'Master']:#, 'Custom']:
            diff_act = QAction(diff, self.diff_group, checkable=True)
            game_menu.addAction(diff_act)
            diff_act.id = diff[0].lower()
            if diff_act.id == self.procr.diff:
                diff_act.setChecked(True)
            diff_act.triggered.connect(lambda e: self.change_difficulty())
            diff_act.setShortcut(diff[0])
        game_menu.addSeparator() #new section
        # Zoom board action
        # zoom_act = QAction('Zoom', self)
        # zoom_act.triggered.connect(SOMETHING)
        # game_menu.addAction(zoom_act)
        # Change styles options
        # styles_menu = QMenu('Styles', self)
        # game_menu.addMenu(styles_menu)
        # for img_group in ['buttons']:
        #     submenu = QMenu(img_group.capitalize(), self)
        #     styles_menu.addMenu(submenu)
        #     group = QActionGroup(self, exclusive=True)
        #     for folder in glob(join(img_direc, img_group, '*')):
        #         style = basename(folder)
        #         style_act = QAction(style, self, checkable=True)
        #         group.addAction(style_act)
        #         # style_act.triggered.connect(SOMETHING)
        #         submenu.addAction(style_act)
        # game_menu.addSeparator()
        exit_act = QAction('Exit', self)
        game_menu.addAction(exit_act)
        exit_act.triggered.connect(self.close)
        exit_act.setShortcut('Alt+F4')
        # OPTIONS MENU
        # First-click success option
        first_act = QAction('Safe start', self, checkable=True)
        opts_menu.addAction(first_act)
        first_act.setChecked(self.procr.first_success)
        first_act.triggered.connect(lambda: setattr(self.procr,
            'first_success', not(self.procr.first_success)))
        # Drag-select option
        drag_act = QAction('Drag-select', self, checkable=True)
        drag_act.setChecked(self.procr.drag_select)
        drag_act.triggered.connect(self.toggle_drag_select)
        opts_menu.addAction(drag_act)
        # Max mines per cell option
        per_cell_menu = QMenu('Max per cell', self)
        opts_menu.addMenu(per_cell_menu)
        self.per_cell_group = QActionGroup(self, exclusive=True)
        for i in range(1, 4):
            action = QAction(str(i), self, checkable=True)
            per_cell_menu.addAction(action)
            self.per_cell_group.addAction(action)
            action.num = i
            if self.procr.per_cell == i:
                action.setChecked(True)
            action.triggered.connect(self.change_per_cell)
        # HELP MENU
        retrieve_act = QAction('Retrieve highscores', self)
        retrieve_act.triggered.connect(self.retrieve_highscores)
        help_menu.addAction(retrieve_act)
    def resize(self):
        width = max(140, self.mf_widget.width()+20)
        height = (self.menubar.height() + self.panel.height()
                  + self.mf_widget.height() + 20 + self.namebar.height())
        self.setFixedSize(width, height)
    def start(self):
        self.move(500, 150)
        self.show() #[Fix jerking]
        self.resize()
        app.exec_()
    def closeEvent(self, event):
        self.procr.close_game()
        event.accept()
    def focus_to_game(self):
        """Move the focus to the main game, away from the name bar or
        probabilities."""
        if self.namebar.isEnabled():
            self.namebar.focus_out()
            return
    def prepare_new_game(self):
        self.timer.stop()
        self.timer.label.setText('000')
        for (x, y) in self.mf_widget.all_coords:
            self.mf_widget.buttons[y][x].refresh()
        self.set_face('ready')
        self.set_mines_counter()
        if 'highscores' in self.open_windows:
            self.open_windows['highscores'].model.set_current_hscore(None)
    def start_game(self):
        self.timer.start()
    def reveal_cell(self, x, y):
        """Make the cell at (x, y) show the same as is contained in the current
        game board."""
        b = self.mf_widget.buttons[y][x]
        contents = self.procr.game.board[y][x]
        if type(contents) is int:
            im_type = 'btn'
            num = contents
        elif type(contents) is str:
            char = contents[0]
            num = int(contents[1])
            # [Put these in a dictionary in utils (or __init__)?]
            if char == 'F':
                im_type = 'flag'
            elif char == 'M':
                im_type = 'mine'
            elif char == '!':
                im_type = 'hit'
            elif char == 'X':
                im_type = 'cross'
            elif char == 'L':
                im_type = 'life'
        b.set_image(im_type, num)
    def flag(self, x, y, n):
        b = self.mf_widget.buttons[y][x]
        b.setPixmap(self.mf_widget.flag_images[n])
        rem_mines = self.procr.mines - self.procr.nr_flags
        self.set_mines_counter()
        if n == 1:
            b.pressed.disconnect()
            b.released.disconnect()
            b.clicked.disconnect()
            b.areaPressed.disconnect()
            b.areaReleased.disconnect()
    def unflag(self, x, y):
        b = self.mf_widget.buttons[y][x]
        b.refresh()
        self.set_mines_counter()
    def set_mines_counter(self):
        rem_mines = self.procr.mines - self.procr.nr_flags
        self.mines_counter.setText('{:03d}'.format(abs(rem_mines)))
        if rem_mines >= 0:
            self.mines_counter.setStyleSheet("""color: red;
                                                background: black;
                                                border-radius: 2px;
                                                font: bold 15px Tahoma;
                                                padding-left: 1px;""")
        else:
            self.mines_counter.setStyleSheet("""color: black;
                                                background: red;
                                                border-radius: 2px;
                                                font: bold 15px Tahoma;
                                                padding-left: 1px;""")
    def set_face(self, state, check_game_state=False):
        if (check_game_state and
            self.procr.game.state not in ['ready', 'active']):
            return False
        life = 1
        fname = 'face' + str(life) + state + '.png'
        pixmap = QPixmap(join(img_direc, 'faces', fname))
        self.face_button.setPixmap(pixmap.scaled(26, 26,
                                         transformMode=Qt.SmoothTransformation))
        return True
    def finalise_loss(self):
        self.set_face('lost')
        self.timer.stop()
        self.timer.set_time(self.procr.game.elapsed)
        for (x, y) in self.mf_widget.all_coords:
            b = self.mf_widget.buttons[y][x]
            b.remove_interaction()
            board_cell = self.procr.game.board[y][x]
            if str(board_cell)[0] in ['M', '!', 'X']:
                self.reveal_cell(x, y)
    def finalise_win(self):
        self.set_face('won')
        self.set_mines_counter()
        self.timer.stop()
        self.timer.set_time(self.procr.game.elapsed)
        # self.timer.set_time(self.procr.game.)
        for (x, y) in self.mf_widget.all_coords:
            b = self.mf_widget.buttons[y][x]
            b.remove_interaction()
            n = self.procr.game.mf[y][x]
            if n > 0:
                self.reveal_cell(x, y)
    def handle_highscore(self, hscore):
        if not self.procr.name:
            popup = QInputDialog(self, flags=Qt.WindowCloseButtonHint)
            popup.setWindowTitle('Name entry')
            popup.setLabelText('Enter your name for the highscores:')
            popup.setInputMode(QInputDialog.TextInput)
            edit = popup.findChild(QLineEdit)
            edit.setMaxLength(12)
            result = popup.exec_()
            text = edit.text()
            if result and text:
                # 'Ok' or return pressed
                self.namebar.setText(text)
                self.namebar.focus_out() #set name to current game and procr
            else:
                # No name submitted, don't show highscores
                return
        # Add completed game to highscores
        self.procr.current_hscores.append(hscore)
        model = self.hscores_window.model
        model.set_current_hscore(self.procr.hscore)
        # Make current highscore bold [and scroll to it]
        filters = self.procr.hscore_filters.copy()
        cut_off = 5 if filters['name'] else 1
        # Show highscores for current name if there's any name filter
        filters['name'] = self.procr.name
        top_in = get_hscore_position(self.procr.hscore, self.procr.game,
                                     filters, cut_off)
        if top_in is not None:
            self.show_highscores()
            # Set temporary sort header and filters
            model.change_sort(top_in, temp=True)
            # Show highscores for current name if there's any name filter
            if self.procr.hscore_filters['name']:
                model.apply_filters({'name': self.procr.name}, temp=True)
    def show_highscores(self, event=None, sort_by=None, filters=None):
        """Show the highscores window (or update if already open)."""
        if self.procr.game.state == 'ready':
            settings_source = self.procr
        else:
            settings_source = self.procr.game
        self.hscores_window.model.update_hscores_group(settings_source)
        # self.hscores_window.model.set_current_hscore(self.procr.hscore)
        self.hscores_window.show()
        self.open_windows['highscores'] = self.hscores_window
        # Remove from open_windows when closed
        def close_hscore_win(event):
            self.hscores_window.hide()
            self.open_windows.pop('highscores')
        self.hscores_window.closeEvent = close_hscore_win
    def set_highscore_settings(self, sort_by=None, filters=None):
        if sort_by is not None:
            self.procr.hscore_sort = sort_by
        if filters is not None:
            self.procr.hscore_filters = filters
    def show_probs(self):
        if self.procr.game.state not in ['active', 'ready']:
            return
        if self.state == 'probs':
            self.clear_probs()
            return
        probs = self.procr.calculate_probs()
        self.state = 'probs'
        for (x, y) in self.mf_widget.all_coords:
            if self.procr.game.board[y][x] != 'U':
                continue
            b = self.mf_widget.buttons[y][x]
            p = probs[y][x]
            # print(p)
            density = self.procr.mines / (self.procr.x_size * self.procr.y_size)
            if p >= density:
                ratio = (p - density)/(1 - density)
                colour = blend_colours(ratio)
            else:
                ratio = (density - p)/density
                colour = blend_colours(ratio, high=(0, 255, 0))
            b.image = self.mf_widget.btn_images['up'].copy() #copy base pixmap
            painter = QPainter(b.image)
            painter.fillRect(2, 2, self.btn_size-4, self.btn_size-4,
                             QColor(*colour))
            if p == 0:
                painter.drawEllipse(4, 4, 7, 7)
            elif p == 1:
                painter.drawLine(4, 4, 11, 11)
                painter.drawLine(4, 11, 11, 4)
            # elif self.btn_size >= 24:
            #     text = '{}%'.format(round(100*p))
            #     painter.drawText(x, y, text)
            b.setPixmap(b.image)
    def clear_probs(self):
        for (x, y) in self.mf_widget.all_coords:
            if self.procr.game.board[y][x] == 'U':
                self.mf_widget.buttons[y][x].set_image('btn', 'up')
        self.state = self.procr.game.state
    def change_difficulty(self):
        diff = self.diff_group.checkedAction().id
        if diff == self.procr.diff:
            return #not changed
        if diff == 'c':
            # Currently does nothing
            # Find the old difficulty button and check it
            for action in self.diff_group.actions():
                if action.id == self.procr.diff:
                    action.setChecked(True)
            return
        self.procr.change_difficulty(diff)
        x, y = self.procr.x_size, self.procr.y_size
        self.mf_widget.reshape(x, y)
        self.resize()
        self.prepare_new_game()
    def toggle_drag_select(self):
        self.procr.change_setting('drag_select', not(self.procr.drag_select))
    def change_per_cell(self):
        self.procr.change_setting('per_cell',
                                  self.per_cell_group.checkedAction().num)
    def retrieve_highscores(self):
        """Add highscores from another distribution without performing checks."""
        #[Improve by giving error message before closing selection popup]
        options = {
            'parent': self,
            'caption': (
                  "Retrieve highscores"
                + ": select the main folder of a previous version"
                # + " (versions >= 1.1.2 only)"
                ),
            'directory': dirname(pkg_direc)
            }
        direc = QFileDialog.getExistingDirectory(**options)
        # print(direc)
        if not direc:
            return #cancelled (presumed)
        def show_msg(msg):
            # print(msg)
            popup = QMessageBox(self)
            popup.setText(msg)
            popup.exec_()
        if not exists(join(direc, 'files')):
            show_msg("Couldn't find folder expected to contain highscores. "
                   + "Be sure to select the main directory - the one which "
                   + "contains the folder named 'files'.")
            return
        try:
            info_path = glob(join(direc, 'files', 'info.*'))[0]
            with open(info_path, 'r') as f:
                info = json.load(f)
            version = info['version']
            in_exe = info['frozen'] if 'frozen' in info else True
        except:
            show_msg("Unknown version, try running the old game first. "
                   + "Contact minegauler@gmail.com if problems persist.")
            return
        if LooseVersion(version) < '1.1.2':
            show_msg("Cannot retrieve highscores from versions older than 1.1.2 - "
                   + "contact minegauler@gmail.com to have old highscores updated.")
            return
        try:
            print(version)
            added = include_old_hscores(direc, version, in_exe)
            show_msg(f"Number of highscores added: {added}")
            save_all_highscores()
        except FileNotFoundError:
            show_msg("Cannot find highscores files. "
                   + "Contact minegauler@gmail.com if you expected this game "
                   + "to have highscores.")


class MinefieldWidget(QWidget):
    def __init__(self, parent, processor, gui, **settings):
        super().__init__(parent)
        self.procr = processor
        self.gui = gui
        self.x_size, self.y_size = self.procr.x_size, self.procr.y_size
        self.all_coords = [(i, j) for i in range(self.x_size)
                           for j in range(self.y_size)]
        self.populate()
        self.get_pixmaps()
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        self.mouse_buttons_down = Qt.NoButton
    def populate(self):
        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.buttons = []
        for j in range(self.y_size):
            row = []
            for i in range(self.x_size):
                b = CellButton(self, i, j)
                self.layout.addWidget(b, j, i)
                row.append(b)
            self.buttons.append(row)
    def make_pixmap(self, fname1, im_type, fname2=None, prop=None):
        def get_path(im_type, fname):
            base = join(img_direc, im_type)
            path = join(base, self.gui.styles[im_type], fname)
            if not exists(path):
                logging.warn(
                    'Missing image file at {}, using standard style.'.format(path))
                path = join(base, 'Standard', fname)
            return path
        path1 = get_path('buttons', fname1)
        if fname2:
            image = QImage(path1).scaled(self.gui.btn_size, self.gui.btn_size,
                                         transformMode=Qt.SmoothTransformation)
            size2 = self.gui.btn_size*prop
            overlay = QPixmap(get_path(im_type, fname2)).scaled(size2, size2,
                                         transformMode=Qt.SmoothTransformation)
            painter = QPainter(image)
            margin = self.gui.btn_size * (1 - prop) / 2
            painter.drawPixmap(margin, margin, overlay)
            painter.end()
            image = QPixmap.fromImage(image)
        else:
            image = QPixmap(path1).scaled(self.gui.btn_size, self.gui.btn_size,
                                          transformMode=Qt.SmoothTransformation)
        return image
    def get_pixmaps(self, required='all'):
        if required in ['all', 'buttons']:
            self.btn_images = dict()
            self.btn_images['up'] = self.make_pixmap('btn_up.png', 'buttons')
            self.btn_images['down'] = self.make_pixmap('btn_down.png', 'buttons')
            self.btn_images[0] = self.btn_images['down']
        if required in ['all', 'numbers', 'buttons']:
            for i in range(1, 19):
                self.btn_images[i] = self.make_pixmap('btn_down.png', 'numbers',
                                                    'num{}.png'.format(i), 7/8)
        if required in ['all', 'markers', 'buttons']:
            self.mine_images = [0]
            self.hit_images = [0]
            self.life_images = [0]
            self.flag_images = [0]
            self.cross_images = [0]
            for i in range(1, 4):
                self.mine_images.append(self.make_pixmap('btn_down.png',
                    'markers', 'mine{}.png'.format(i), 7/8))
                self.hit_images.append(self.make_pixmap('btn_down_hit.png',
                    'markers', 'mine{}.png'.format(i), 7/8))
                self.life_images.append(self.make_pixmap('btn_down_life.png',
                    'markers', 'mine{}.png'.format(i), 7/8))
                self.flag_images.append(self.make_pixmap('btn_up.png',
                    'markers', 'flag{}.png'.format(i), 5/8))
                self.cross_images.append(self.make_pixmap('btn_up.png',
                    'markers', 'cross{}.png'.format(i), 5/8))
    def mousePressEvent(self, event):
        self.gui.focus_to_game()
        x, y = event.x() // self.gui.btn_size, event.y() // self.gui.btn_size
        self.mouse_coord = (x, y)
        b = self.buttons[y][x]
        self.mouse_buttons_down = QMouseButton_to_int(event.buttons())
        if self.mouse_buttons_down == int(Qt.LeftButton):
            self.both_mouse_buttons_pressed = False
            if self.procr.drag_select:
                self.gui.set_face('active', check_game_state=True)
            b.pressed.emit()
        elif self.mouse_buttons_down == int(Qt.RightButton):
            self.both_mouse_buttons_pressed = False
            b.rightPressed.emit()
        elif self.mouse_buttons_down == int(Qt.LeftButton | Qt.RightButton):
            self.both_mouse_buttons_pressed = True
            # Reset face to account for case drag_select=True
            self.gui.set_face('ready', check_game_state=True)
            self.sink_area(x, y)
            if self.procr.drag_select:
                self.procr.chord(x, y)
    def mouseReleaseEvent(self, event):
        if not self.mouse_coord:
            return # Do nothing it not currently over a button
        x, y = self.mouse_coord
        self.mouse_coord = None
        self.mouse_buttons_down -= QMouseButton_to_int(event.button()) #[FIX THIS (BUG)]
        b = self.buttons[y][x]
        # Catch a case for drag_select=True (left-down always active)
        self.gui.set_face('ready', check_game_state=True)
        if self.mouse_buttons_down != int(Qt.NoButton): # Both buttons were down
            self.raise_area(x, y)
            if not self.procr.drag_select:
                self.procr.chord(x, y)
            elif self.procr.drag_select and event.button() == Qt.RightButton:
                self.gui.set_face('active', check_game_state=True)
        elif event.button() == Qt.LeftButton:
            if self.procr.drag_select or not self.both_mouse_buttons_pressed:
                b.clicked.emit()
    def mouseMoveEvent(self, event):
        old_coord = self.mouse_coord
        x, y = event.x() // self.gui.btn_size, event.y() // self.gui.btn_size
        # Update mouse_coord
        self.mouse_coord = (x, y) if (x, y) in self.all_coords else None
        if old_coord != self.mouse_coord:
            if (event.buttons() != Qt.LeftButton | Qt.RightButton
                and self.both_mouse_buttons_pressed and not self.procr.drag_select):
                # Do nothing if both buttons were pressed but aren't currently
                return
            if old_coord:
                old_x, old_y = old_coord
                if event.buttons() == Qt.LeftButton:
                    self.buttons[old_y][old_x].released.emit()
                elif event.buttons() == Qt.LeftButton | Qt.RightButton:
                    self.raise_area(old_x, old_y)
            if self.mouse_coord:
                if event.buttons() == Qt.LeftButton:
                    self.buttons[y][x].pressed.emit()
                elif event.buttons() == Qt.RightButton and self.procr.drag_select:
                    self.buttons[y][x].rightPressed.emit()
                elif event.buttons() == Qt.LeftButton | Qt.RightButton:
                    self.sink_area(x, y)
    def sink_area(self, x, y):
        for (i, j) in get_nbrs(x, y, self.x_size, self.y_size):
            self.buttons[j][i].areaPressed.emit()
    def raise_area(self, x, y):
        for (i, j) in get_nbrs(x, y, self.x_size, self.y_size):
            self.buttons[j][i].areaReleased.emit()
    def reshape(self, x_size, y_size):
        old_x, old_y = self.x_size, self.y_size
        self.x_size, self.y_size = x_size, y_size
        self.all_coords = [(i, j) for i in range(x_size) for j in range(y_size)]
        # New buttons to be created
        # First add on to the end of every row that already exists
        for j, row in enumerate(self.buttons):
            for i in range(len(row), x_size): #extra in x-direction
                b = CellButton(self, i, j)
                self.layout.addWidget(b, j, i)
                row.append(b)
        # Next create any new rows that are needed at same length as the others
        for j in range(len(self.buttons), y_size):
            row = []
            for i in range(len(self.buttons[0])): #keep self.buttons square
                b = CellButton(self, i, j)
                self.layout.addWidget(b, j, i)
                row.append(b)
            self.buttons.append(row)
        # Buttons to be hidden/shown
        for x in range(max(old_x, x_size)):
            for y in range(max(old_y, y_size)):
                if x < x_size and y < y_size:
                    self.buttons[y][x].setVisible(True)
                else:
                    self.buttons[y][x].setVisible(False)
        self.setFixedSize(x_size*self.gui.btn_size, y_size*self.gui.btn_size)

class CellButton(QLabel):
    pressed = pyqtSignal()      # Left mouse button pressed down over button
    released = pyqtSignal()     # Left mouse button moved away from button
    clicked = pyqtSignal()      # Left mouse button released over button
    rightPressed = pyqtSignal() # Right mouse button pressed down
    areaPressed = pyqtSignal()  # Both mouse buttons down on a button in area
    areaReleased = pyqtSignal() # Area release (move away/raise mouse button...)
    def __init__(self, parent, x, y):
        super().__init__(parent)
        self.parent = parent #stores data such as images, settings
        self.gui = parent.gui
        self.procr = parent.procr
        # self.setFixedSize(self.gui.btn_size, self.gui.btn_size)
        self.x, self.y = x, y
    def press(self):
        if self.procr.drag_select:
            self.procr.click(self.x, self.y)
            if self.gui.state == 'probs':
                # self.gui.state = 'oldprobs'
                self.gui.clear_probs()
                self.gui.show_probs()
        else:
            self.gui.set_face('active')
            self.setPixmap(self.parent.btn_images['down'])
    def release(self):
        self.gui.set_face('ready')
        self.setPixmap(self.parent.btn_images['up'])
    def click(self):
        self.gui.set_face('ready')
        self.procr.click(self.x, self.y)
        if self.gui.state == 'probs':
            # self.gui.state = 'oldprobs'
            self.gui.clear_probs()
            self.gui.show_probs()
    def rightPress(self):
        self.procr.toggle_flag(self.x, self.y)
    def areaPress(self):
        self.gui.set_face('active')
        self.setPixmap(self.parent.btn_images['down'])
    def refresh(self):
        self.set_image('btn', 'up')
        # First remove connections so that signals are only connected once.
        self.remove_interaction()
        self.pressed.connect(self.press)
        self.released.connect(self.release)
        self.clicked.connect(self.click)
        self.rightPressed.connect(self.rightPress)
        self.areaPressed.connect(self.areaPress)
        self.areaReleased.connect(self.release)
    def remove_interaction(self):
        """Remove all connected signals for interation through clicks."""
        for signal in ['pressed', 'released', 'clicked', 'rightPressed',
                       'areaPressed', 'areaReleased']:
            try:
                getattr(self, signal).disconnect()
            except TypeError:
                pass # Already disconnected
    def set_image(self, im_type, key):
        if key != 'up':
            self.remove_interaction()
        images = getattr(self.parent, im_type + '_images')
        self.setPixmap(images[key])

class TopPanel(QAbstractButton):
    def __init__(self, parent, gui):
        super().__init__(parent)
        self.gui = gui
        self.setFixedHeight(40)
        self.populate()
        self.pressed.connect(self.press)
        self.released.connect(self.release)
        self.clicked.connect(self.gui.procr.prepare_new_game)
    def paintEvent(self, e):
        # Must be implemented on QAbstractButton
        pass
    def sizeHint(self):
        return QSize(100, 40)
    def populate(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setAlignment(Qt.AlignCenter)
        self.gui.mines_counter = self.mines_counter = QLabel(self)
        self.mines_counter.setFixedSize(39, 26)
        layout.addWidget(self.mines_counter)
        layout.addStretch()
        self.gui.face_button = self.face_button = QLabel(self)
        self.face_button.setFixedSize(32, 32)
        self.face_button.setFrameShape(QFrame.Panel)
        self.face_button.setFrameShadow(QFrame.Raised)
        self.face_button.setLineWidth(3)
        layout.addWidget(self.face_button)
        layout.addStretch()
        self.gui.timer = self.timer = Timer(self)
        # self.timer = QLabel('000', self)
        # self.timer.setFixedSize(39, 26)
        # self.timer.setStyleSheet("""color: red;
        #                             background: black;
        #                             border-radius: 2px;
        #                             font: bold 15px Tahoma;
        #                             padding-left: 1px;""")
        layout.addWidget(self.timer.label)
    @pyqtSlot()
    def press(self):
        self.gui.face_button.setFrameShadow(QFrame.Sunken)
        # self.gui.focus_to_game()
    @pyqtSlot()
    def release(self):
        self.gui.face_button.setFrameShadow(QFrame.Raised)

class Timer(QTimer):
    def __init__(self, parent):
        super().__init__()
        self.label = QLabel('000', parent)
        self.label.setFixedSize(39, 26)
        self.label.setStyleSheet("""color: red;
                                    background: black;
                                    border-radius: 2px;
                                    font: bold 15px Tahoma;
                                    padding-left: 1px;""")
        self.timeout.connect(self.update)
    def start(self):
        self.start_time = tm.time()
        super().start(100) #update every 0.1 seconds
    def update(self):
        elapsed = tm.time() - self.start_time
        self.set_time(elapsed)
    def set_time(self, time):
        self.label.setText('{:03d}'.format(min(int(time) + 1, 999)))

class NameBar(QLineEdit):
    def __init__(self, parent, gui):
        super().__init__(parent)
        self.gui = gui
        self.setAlignment(Qt.AlignCenter)
        self.font = QFont()
        self.font.setBold(True)
        self.setFont(self.font)
        self.setPlaceholderText('Enter name here')
        self.setMaxLength(12)
        self.setFocusPolicy(Qt.NoFocus) #only focus in by double-clicking
        if self.gui.procr.name:
            self.setText(self.gui.procr.name)
        else:
            self.setFocus()
        self.returnPressed.connect(self.focus_out)
    def focus_out(self):
        self.clearFocus()
        self.deselect()
        procr = self.gui.procr
        old_name = procr.name
        procr.name = procr.game.name = self.text().strip()
        if procr.hscore:
            h = procr.hscore
            h['name'] = procr.name
            h['key'] = enchs(procr.game, h)
            if procr.name:
                if not old_name:
                    # Add to highscores now there's a name
                    procr.current_hscores.append(h)
                self.gui.hscores_window.model.set_current_hscore(h)
            else:
                if procr.current_hscores[-1] == h:
                    # Remove from highscores as there's now no name
                    procr.current_hscores.pop()
                self.gui.hscores_window.model.set_current_hscore(None)
        if procr.hscore_filters['name']:# == old_name:
            # Change highscores name filter to new name
            # Satisfies case of temporary name filter too
            self.gui.hscores_window.model.apply_filters({'name': procr.name})
    def mouseDoubleClickEvent(self, event):
        self.selectAll()
        self.setFocus()



if __name__ == '__main__':
	# app = QApplication(sys.argv)
    from minegauler.dummies import DummyProcessor
    from minegauler.utils import default_settings
    win = GameGUI(DummyProcessor(**default_settings))
    win.prepare_new_game()
    win.start()
