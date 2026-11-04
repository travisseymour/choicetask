"""
ChoiceTask
Copyright (C) 2015-2026 Travis L. Seymour, PhD

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

import os
import random

from choicetask import exptobj, log
from choicetask.colordict import rgbcolor
from choicetask.mboxes import mbox_warning


def shuffle_with_max_consecutive(
    items: list, key_func: callable, max_consecutive: int = 2, max_attempts: int = 1000
) -> list:
    """
    Shuffle a list while preventing more than max_consecutive items with the same key in a row.

    Args:
        items: List of items to shuffle
        key_func: Function to extract the grouping key from each item (e.g., lambda x: x[0] for color)
        max_consecutive: Maximum allowed consecutive items with the same key
        max_attempts: Maximum shuffle attempts before falling back to simple shuffle

    Returns:
        Shuffled list meeting the constraint, or best-effort shuffle if constraint can't be met
    """
    rng = random.Random()

    for _ in range(max_attempts):
        shuffled = items.copy()
        rng.shuffle(shuffled)

        # Check if this shuffle meets the constraint
        valid = True
        for i in range(len(shuffled) - max_consecutive):
            keys = [key_func(shuffled[j]) for j in range(i, i + max_consecutive + 1)]
            if len(set(keys)) == 1:  # All same key
                valid = False
                break

        if valid:
            return shuffled

    # Fallback: construct a valid sequence if possible
    shuffled = items.copy()
    rng.shuffle(shuffled)

    # Try to fix violations by swapping
    for _ in range(max_attempts):
        fixed = True
        for i in range(len(shuffled) - max_consecutive):
            keys = [key_func(shuffled[j]) for j in range(i, i + max_consecutive + 1)]
            if len(set(keys)) == 1:
                # Find a position to swap with
                for swap_idx in range(i + max_consecutive + 1, len(shuffled)):
                    if key_func(shuffled[swap_idx]) != keys[0]:
                        shuffled[i + max_consecutive], shuffled[swap_idx] = (
                            shuffled[swap_idx],
                            shuffled[i + max_consecutive],
                        )
                        fixed = False
                        break
        if fixed:
            break

    return shuffled


class PsychTask:
    """Implements Base Structure of a Simple Console-Based Experiment"""

    # Initialize
    def __init__(
        self,
        surface,
        session_id,
        trial_list,
        allowed,
        condition,
        instructions,
        blocks,
        trial_feedback=True,
        block_feedback=True,
        overwrite=False,
        save_path=".",
        stim_diameter=25,
        tag="default",
    ):
        # Session Settings Variables
        self.surface = surface
        self.session_id = session_id
        self.trial_list = trial_list
        self.allowed = allowed
        self.condition = condition
        self.instructions = instructions
        self.blocks = blocks
        self.trial_feedback = trial_feedback
        self.block_feedback = block_feedback
        self.stim_diameter = stim_diameter
        # Session State Variables
        self.current_block = 0
        self.current_trial = 0
        self.quit_now = False
        self.datalist = []
        self.block_rt = []
        self.block_acc = []
        self.header = "WARNING: NO HEADER SET, TO FIX, SET self.header IN runBlock()"
        self.overwrite = overwrite
        self.save_path = save_path
        self.tag = tag

    # Runs the entire session by calling other methods
    def run_session(self):
        # Show instructions
        my_trial_event = exptobj.PictureTrialEvent(
            surface=self.surface,
            params={
                "picfile": self.instructions,
                "location": (None, None),
                "backcolor": rgbcolor["Black"],
                "fullscreen": True,
            },
            stopinfo={"keypress": [" "]},
        )
        my_trial_event.run()
        """run all trial in all blocks"""
        for a_block in range(self.blocks):
            self.run_block()
        self.save_data()
        if not self.quit_now:
            my_trial_event = exptobj.MultilineTextTrialEvent(
                surface=self.surface,
                params={
                    "message": "The Experiment is Over,\nThanks for your Participation.\n\n\n\n\n\n\n\nPress Q to exit",
                    "fontname": "Arial",
                    "fontsize": 32,
                    "backcolor": rgbcolor["Black"],
                },
                stopinfo={"keypress": ["q"]},
            )
            my_trial_event.run()

    # Run Block
    def run_block(self):
        """run all blocks"""
        # init block stats vars
        self.block_rt = []
        self.block_acc = []
        # if ready to quit, skip this block
        if self.quit_now:
            return
        # Randomizes trial list (max 2 consecutive same-color trials)
        self.trial_list = shuffle_with_max_consecutive(
            self.trial_list, key_func=lambda x: x[0], max_consecutive=2
        )
        # Advances the block counter
        self.current_block += 1
        # Pre-block mask
        my_trial_event = exptobj.TextTrialEvent(
            surface=self.surface, params={"message": " ", "fontname": "Arial"}, stopinfo={"timelimit": 2}
        )
        my_trial_event.run()
        # Runs all trials by calling run trial method
        for atrial in self.trial_list:
            if self.quit_now:
                break
            self.run_trial(atrial)  # atrial something like ("Red", "Easy", "u")
        # show block feedback
        if self.block_feedback:
            if not len(self.block_rt):
                block_rt_avg = 0
            else:
                block_rt_avg = int(sum(self.block_rt) / len(self.block_rt))
            if self.block_acc:
                block_acc = int(float(sum(self.block_acc)) / float(len(self.block_acc)) * 100)
            else:
                block_acc = 0
            feedback_msg = (
                f"Block Feedback [{self.current_block} of {self.blocks}]\n"
                "---------------------\n"
                f"Average Response Time: {block_rt_avg} milliseconds.\n"
                f"    Response Accuracy: {block_acc} percent."
                "\n\n\n\n\n"
                "Press SpaceBar To Start Next Block"
            )
            fs = 40
            w, h = self.surface.get_width(), self.surface.get_height()
            if (w, h) == (640, 480):
                fs = 32
            my_trial_event = exptobj.MultilineTextTrialEvent(
                surface=self.surface,
                params={
                    "message": feedback_msg,
                    "fontname": "Arial",
                    "fontsize": fs,
                    "fontcolor": rgbcolor["Cyan"],
                    "backcolor": rgbcolor["Black"],
                },
                stopinfo={"keypress": [" "]},
            )
            my_trial_event.run()

    def run_trial(self, trial_info):
        # you probably want to set self.header depending on how you overload this method
        pass

    def save_data(self):
        # craft filename
        filename = f"{self.session_id}_mhpchoicetask_data.csv"
        # construct full data path
        out_filename = os.path.join(self.save_path, filename)
        mode = "w"
        if os.path.exists(out_filename) and not self.overwrite:
            mode = "a"
        try:
            with open(out_filename, mode) as outfile:
                if mode == "w":
                    outfile.write(self.header + "\n")
                for a_row in self.datalist:
                    a_row_string = ",".join(a_row) + "\n"
                    outfile.write(a_row_string)
            log.info(f"Data successfully saved to {out_filename}")
        except OSError:
            comment = f"Warning: Unable to save data file to [<em>{out_filename}</em>]"
            log.error(f"\n\nDATA LOSS NOTICE:{comment}\n\n")
            mbox_warning(msg=comment, title="Data Loss Notice")
