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

import datetime
import random

from PySide6.QtWidgets import QApplication

from choicetask import exptobj
from choicetask.colordict import rgbcolor
from choicetask.psychtaskclass import PsychTask
from choicetask.version import __version__


class ChoiceTask(PsychTask):
    """4-Color Choice Task |  Red-Green-Blue-Yellow --> U I O P"""

    def run_trial(self, trial_info):
        # Checks that trial info exists and is for current condition.
        if trial_info and len(trial_info) == 4:
            colorname, condition, correct_resp, x_offset = trial_info
            x_offset *= self.stim_diameter
            if not x_offset:
                xpos = None
            if condition == self.condition:
                # Advances the trial counter
                self.current_trial += 1
                # Present Fixation Stimulus for 500 ms
                my_trial_event = exptobj.TextTrialEvent(
                    surface=self.surface,
                    params={"message": "+", "fontname": "Arial", "fontsize": 40, "backcolor": rgbcolor["Black"]},
                    stopinfo={"timelimit": 0.5},
                )
                my_trial_event.run()
                # Present stimulus and collect RT
                my_trial_event = exptobj.CircleTrialEvent(
                    surface=self.surface,
                    params={
                        "color": rgbcolor[colorname.title()],
                        "backcolor": rgbcolor["Black"],
                        "radius": self.stim_diameter // 2,
                        "offset": x_offset,
                    },
                    stopinfo={"keypress": self.allowed, "timelimit": 6},
                )
                response, rt = my_trial_event.run()
                # Convert RT to ms
                rt = int(rt * 1000.0)
                # Handle Quit Signal
                if response == "quit":
                    self.quit_now = True
                    return
                # Judges Accuracy (Correct or Incorrect)
                if response == correct_resp:
                    outcome = "Correct"
                    # update block RT list (correct RTs only)
                    self.block_rt.append(rt)
                else:
                    outcome = "Incorrect"
                # update block acc
                self.block_acc.append(int(outcome == "Correct"))

                # Show participant the outcome and RT
                if self.trial_feedback:
                    msg = f"{outcome}, RT = {rt} ms"
                    my_trial_event = exptobj.TextTrialEvent(
                        surface=self.surface,
                        params={"message": msg, "fontname": "Arial", "fontsize": 30, "backcolor": rgbcolor["Black"]},
                        stopinfo={"keypress": [" "], "timelimit": 2},
                    )
                    my_trial_event.run()
                # Update data list with this trial's data
                if type(response) is not str:
                    response = ""
                self.header = (
                    "DATE,TIME,ID,BLOCK,TRIAL,STIM,XLOC,COND,CRESP,RESP,RT,ACC,MAXTRIAL,MAXBLOCK,"
                    "TRIALFEEDBACK,BLOCKFEEDBACK,STIMSIZE,SCRNWIDTH,SCRNHEIGHT,VERSION,TAG"
                )
                the_date = datetime.datetime.today().strftime("%m-%d-%Y")
                the_time = datetime.datetime.now().strftime("%I:%M:%S %p")
                screen = QApplication.primaryScreen()
                size = screen.size()
                w, h = size.width(), size.height()
                trial_data = (
                    the_date,
                    the_time,
                    self.session_id,
                    self.current_block,
                    self.current_trial,
                    colorname,
                    x_offset // self.stim_diameter,
                    condition,
                    correct_resp,
                    response,
                    rt,
                    outcome,
                    len(self.trial_list),
                    self.blocks,
                    int(self.trial_feedback),
                    int(self.block_feedback),
                    int(self.stim_diameter),
                    int(w),
                    int(h),
                    __version__,
                    self.tag,
                )
                trial_data = map(str, trial_data)  # make sure every element in trial_data is a string using map()
                self.datalist.append(trial_data)
                # Present Inter Trial Interval for 800 to 1300 ms
                rng = random.Random()
                iti_duration = rng.uniform(0.8, 1.3)
                my_trial_event = exptobj.TextTrialEvent(
                    surface=self.surface,
                    params={"message": " ", "fontname": "Arial"},
                    stopinfo={"timelimit": iti_duration},
                )
                my_trial_event.run()
