"""
ChoiceTask
Copyright (C) 2015-2025 Travis L. Seymour, PhD

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from pathlib import Path
from typing import Optional, Union
import os
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from pygame import Surface, SurfaceType

from choicetask import log
from choicetask.app_utils import get_default_font
from choicetask.resource import get_resource
from choicetaskclass import ChoiceTask
from mboxes import mbox_critical
import pygame

# from pygame.locals import *
import configparser
import tempfile
import getpass

app: Optional[QApplication] = None
main_surface: Optional[Union[Surface, SurfaceType]] = None


def user_folder_list(folder_list) -> tuple[str, ...]:
    """
    Find a config/data path that works.

    folder_list is a list of folder names (e.g., ['Documents', 'Desktop']) in order of preference.
    returns tuple of readable and writable paths using supplied folder names.
    """
    # Create list of candidate folders
    candidates = [Path.home() / f for f in folder_list]
    # Also consider the current working directory as a last resort
    candidates.append(Path.cwd())

    # Determine which paths are readable and writable
    good_ones = []
    for adir in candidates:
        if adir.is_dir():
            try:
                with tempfile.TemporaryFile(dir=adir):
                    good_ones.append(str(adir))  # Convert Path to string for consistency
            except (PermissionError, OSError):
                pass  # Not writable

    return tuple(good_ones)


def user_sub_folder(folder_list: str, sub_folder_name: str):
    """
    Finds a valid user directory and attempts to create & test a specified subfolder.

    :param folder_list: List of folder names (e.g., ['Documents', 'Desktop']) in order of preference.
    :param sub_folder_name: Name of the subfolder to create/test in the valid directories.
    :return: Leftmost folder that works, or None if none are suitable.
    """
    good_ones = user_folder_list(folder_list)
    if good_ones:
        for adir in good_ones:
            candidate = Path(adir) / sub_folder_name

            # Check if the directory exists and is writable
            if candidate.is_dir():
                try:
                    with tempfile.TemporaryFile(dir=candidate):
                        return str(candidate)  # Readable and writable
                except (PermissionError, OSError):
                    pass  # Not writable

            # Try to create the directory and check if it's writable
            if not candidate.exists():
                try:
                    candidate.mkdir(parents=True, exist_ok=True)  # Prevent race conditions
                    with tempfile.TemporaryFile(dir=candidate):
                        return str(candidate)
                except (PermissionError, OSError):
                    pass  # Not writable or cannot be created

    return None  # No valid directory found


def default_config():
    """
    Return the default settings for Choice Task
    """

    # Defaults for screen size and stim size are dynamically computed
    screen = QApplication.instance().primaryScreen()
    size = screen.size()
    w, h = size.width(), size.height()
    stim_ratio = 0.023438  # 60 / 2560 (which looks right on my monitor)

    config = configparser.ConfigParser()
    # config.add_section('DEFAULT')
    config.set("DEFAULT", "pid", getpass.getuser().replace(" ", "_"))
    config.set("DEFAULT", "blocks", "4")
    config.set("DEFAULT", "blocktrials", "30")
    config.set("DEFAULT", "condition", "Hard")
    config.set("DEFAULT", "type", "Practice")
    config.set("DEFAULT", "diameter", str(int(stim_ratio * w)))
    config.set("DEFAULT", "width", str(w))
    config.set("DEFAULT", "height", str(h))
    config.set("DEFAULT", "fullscreen", "yes")
    config.set("DEFAULT", "overwrite", "no")
    config.set("DEFAULT", "tag", "Default")

    config.add_section("USER")
    config.set("USER", "pid", getpass.getuser().replace(" ", "_"))
    config.set("USER", "blocks", "4")
    config.set("USER", "blocktrials", "30")
    config.set("USER", "condition", "Hard")
    config.set("USER", "type", "Practice")
    config.set("USER", "diameter", str(int(stim_ratio * w)))
    config.set("USER", "width", str(w))
    config.set("USER", "height", str(h))
    config.set("USER", "fullscreen", "yes")
    config.set("USER", "overwrite", "no")
    config.set("USER", "tag", "Default")

    return config


def load_config_file(config_file, section, expected):
    """
    Setup, init, and possibly load existing config data. Otherwise, default.
    :return: config_path, config_file, config (ConfigParser() instance)
    """
    # create ConfigParser Instance
    config = configparser.ConfigParser()

    use_default = True
    # see if config_file is readable
    if os.path.exists(config_file) and os.path.isfile(config_file):
        # pull params from it
        clist = config.read(config_file)
        # if you got something, see if it's valid
        if clist:
            # try locating the USER section
            if config and section in config.sections():
                # try locating all of the expected parameters
                param_list = expected
                if False not in [config.has_option(section, param) for param in param_list]:
                    use_default = False

    if use_default:
        # none of the above worked, use default
        config = default_config()

    return config


def main():
    global app
    global main_surface
    app = QApplication([])

    default_font = get_default_font(family="sans-serif", size=14)
    QApplication.instance().setFont(default_font)

    from choicetask.sideparam import NoteItem, StringItem, IntItem, ChoiceItem, BoolItem, ParamForm, run_app

    # Load application icons
    icon = QIcon()
    icon.addFile(get_resource("icons", "icon.png"), QSize(16, 16))
    app.setWindowIcon(icon)

    # try to find a save folder
    save_path = user_sub_folder(["Documents", "Desktop"], "mhpchoice")

    # Failed, Quit
    if not save_path:
        comment = "Error: Unable to write to Documents or Desktop folder. Can't proceed without a place to save data."
        mbox_critical(msg=comment, title="Critical Error")

    # Succeeded, Continue
    else:
        # get existing config (else default one)
        configfile = os.path.join(save_path, "mhpchoicetask.ini")
        config = load_config_file(
            configfile,
            "USER",
            ["pid", "blocks", "blocktrials", "condition", "type", "diameter", "width", "fullscreen", "overwrite"],
        )

        # create some lists we'll need
        # conditions = ("Easy", "Hard")
        # session_types = ("Practice", "Test")
        # res_list = [(640, 480), (800, 600), (1024, 768), (1152, 864), (1280, 1024), (2048, 1536),
        #                 (1280, 800), (1440, 900), (1600, 900), (1680, 1050),
        #                 (1920, 1080), (2048, 1152), (2560, 1600)]
        screen = app.primaryScreen()
        size = screen.size()
        w, h = size.width(), size.height()
        # stim_ratio = 0.023438  # 60 / 2560 (which looks right on my monitor)

        # @@@@@@@@@@@@@@@@@@@2

        # Get all available screens
        screens = app.screens()

        # Retrieve screen geometries
        screen_geometries = [
            (screen.geometry().x(), screen.geometry().y(), screen.geometry().width(), screen.geometry().height())
            for screen in screens
        ]

        res_list = []

        # Print screen details
        for idx, (x, y, width, height) in enumerate(screen_geometries):
            print(f"Screen {idx}: Position ({x}, {y}), Size {width}x{height}")
            res_list.append((width, height))

        # @@@@@@@@@@@@@@@@@@@@@@

        # res_list = [(w, h)]

        res_str_list = [f"{x} x {y} (Ratio={(x * 1.0) / y:.2f})" for x, y in res_list]

        # Define parameter widgets
        note = NoteItem(None, note_text="<b>Select Session Parameters</b><p>")
        # '<em>You can hover over the fields for help.</em>')
        pard_id = StringItem("Participant ID", default=config.get("USER", "pid"), notempty=True, maxlength=30)
        blocks = IntItem("Blocks", minimum=1, maximum=10, default=config.getint("USER", "blocks"))
        trials = IntItem("Trials Per Block", minimum=4, maximum=60, default=config.getint("USER", "blocktrials"))
        cond = ChoiceItem("Condition", choices=["Easy", "Hard"], default=config.get("USER", "condition"))
        session_type = ChoiceItem("Session Type", choices=["Practice", "Test"], default=config.get("USER", "type"))
        diameter = IntItem(
            "Circle Diameter",
            minimum=config.getint("USER", "diameter"),
            maximum=config.getint("USER", "diameter"),
            default=config.getint("USER", "diameter"),
        )
        x, y = config.getint("USER", "width"), config.getint("USER", "height")
        res_str = f"{x} x {y} (Ratio={(x * 1.0) / y:.2f})"
        try:
            default = res_str_list.index(res_str)
        except:
            default = res_str_list[0]
        resol = ChoiceItem("Screen Resolution", choices=res_str_list, default=default)
        fullscreen = BoolItem("", tag="Run Fullscreen?", default=config.getboolean("USER", "fullscreen"), enabled=False)
        overwrite = BoolItem("", tag="Overwrite Data If Exists?", default=config.getboolean("USER", "overwrite"))
        tag = StringItem("Data Tag", default=config.get("USER", "tag"), maxlength=40)

        # Create parameter GUI
        param = ParamForm(
            "Settings", [note, pard_id, blocks, trials, cond, session_type, diameter, resol, fullscreen, overwrite, tag]
        )

        old_vals = param.get_values()
        _, v_pid, v_blocks, v_trials, v_cond, v_session_type, v_diameter, v_resol, v_fullscreen, v_overwrite, v_tag = (
            old_vals
        )
        new_vals = param.get_values()
        go_flight = False
        run_app(param, "Settings", app)
        if param.ok:
            # unpack values
            new_vals = param.get_values()
            # [None, u'P100', 2, 4, u'Easy', u'Practice', u'1024 x 768 (Ratio=1.33)', False, False]
            (
                _,
                v_pid,
                v_blocks,
                v_trials,
                v_cond,
                v_session_type,
                v_diameter,
                v_resol,
                v_fullscreen,
                v_overwrite,
                v_tag,
            ) = new_vals
            # correct for trials not div by 4
            if v_trials % 4:
                v_trials = v_trials + 2
            # Verify params with user
            if param.verify():
                go_flight = True

        # Save param changes
        param_changed = old_vals != new_vals
        if param_changed:
            # start with new one so we know defaults are correct
            new_config = default_config()
            # now make changes from this run
            new_config.set("USER", "pid", str(v_pid))
            new_config.set("USER", "blocks", str(v_blocks))
            new_config.set("USER", "blocktrials", str(v_trials))
            new_config.set("USER", "condition", v_cond)
            new_config.set("USER", "type", v_session_type)
            new_config.set("USER", "diameter", str(v_diameter))
            new_config.set("USER", "width", str(res_list[res_str_list.index(v_resol)][0]))
            new_config.set("USER", "height", str(res_list[res_str_list.index(v_resol)][1]))
            new_config.set("USER", "fullscreen", str(v_fullscreen))
            new_config.set("USER", "overwrite", str(v_overwrite))
            new_config.set("USER", "tag", str(v_tag))
            # save config file changes
            if configfile:
                try:
                    with open(configfile, "w") as outfile:
                        new_config.write(outfile)
                    log.info(f"Successfully saved updates to configfile: [{configfile}]")
                except Exception as e:
                    log.error(f"Error: Unable to save updates to configfile: [{configfile}]\n\t{e}")

        # Run Task
        if go_flight:
            easy_stim = [("Red", "Easy", "u"), ("Green", "Easy", "i"), ("Blue", "Easy", "o"), ("Yellow", "Easy", "p")]
            hard_stim = [("Red", "Hard", "u"), ("Green", "Hard", "i"), ("Blue", "Hard", "o"), ("Yellow", "Hard", "p")]

            iterations = v_trials // 4
            if v_cond == "Easy":
                my_stimuli = easy_stim
                pos_offsets = [0] * 5
            else:
                my_stimuli = hard_stim
                pos_offsets = [-2, -1, 0, 1, 2]

            my_stimuli *= iterations
            pos_offsets *= iterations

            # add alternating position offsets to hard_stim list
            my_stimuli = [(clr, cond, key, pos_offsets.pop()) for clr, cond, key in my_stimuli]

            instruction_file = get_resource("images", "instructions.png")

            # show instruction_file
            if os.path.isfile(instruction_file):
                # init pygame
                pygame.init()
                # run task
                if v_fullscreen:
                    fs = pygame.FULLSCREEN
                else:
                    fs = 0
                main_surface = pygame.display.set_mode(res_list[res_str_list.index(v_resol)], fs)
                my_expt = ChoiceTask(
                    surface=main_surface,
                    session_id=v_pid.strip(),
                    trial_list=my_stimuli,
                    allowed=("u", "i", "o", "p"),
                    condition=v_cond,
                    instructions=instruction_file,
                    blocks=v_blocks,
                    trial_feedback=(v_session_type == "Practice"),
                    block_feedback=True,
                    overwrite=v_overwrite,
                    save_path=save_path,
                    stim_diameter=v_diameter,
                    tag=v_tag,
                )
                pygame.mouse.set_visible(False)
                my_expt.run_session()
                pygame.mouse.set_visible(True)
                # shutdown pygame
                pygame.quit()
            else:
                comment = "Error: Unable to locate [<em>instructions.png</em>] inside application bundle."
                mbox_critical(msg=comment, title="Critical Error")


if __name__ == "__main__":
    main()
