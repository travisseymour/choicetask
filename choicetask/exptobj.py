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

from typing import Optional

import pygame
import timeit
import os

from choicetask import log

"""
Classes defining various graphical events for a psych experiment using pygame
"""


class TrialEvent:
    """Psych Experiment Trial Event, Requires valid pygame surface"""

    def __init__(self, surface, params, stopinfo=None):
        """
        surface = pygame surface [REQUIRED]
        params: dictionary of event parameters [REQUIRED]
        stopinfo: dictionary of stopping parameters
        """
        self.surface = surface
        self.params = params
        self.stopinfo = stopinfo

        self.star_time = 0
        self.draw_info = {}
        self.paramsOK = self.validate_params()

    def validate_params(self):
        return True

    def ready_to_stop(self):
        """
        Returns true if conditions for stopping are met.
        Responds to pygame.QUIT no matter what.
        """
        # example: stopinfo={'keypress':['a','b'], 'timelimit': 3}
        ev = pygame.event.poll()

        # window quit signal
        if ev.type == pygame.QUIT:
            return "quit"
        # Shift-X quit signal
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_x:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                return "quit"
        # # Shift-F fullscreen toggle
        # elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_f:
        #     mods = pygame.key.get_mods()
        #     if mods & pygame.KMOD_SHIFT:
        #         pygame.display.toggle_fullscreen()

        # handle stop conditions
        if self.stopinfo:
            if "keypress" in self.stopinfo:
                if ev.type == pygame.KEYDOWN and ev.unicode in self.stopinfo["keypress"]:
                    return str(ev.unicode)

            if "timelimit" in self.stopinfo:
                duration = timeit.default_timer() - self.star_time
                if duration > self.stopinfo["timelimit"]:
                    return duration

        return ""

    def setup_visual_objects(self):
        return None

    def draw_visual_objects(self):
        return  # test: self.surface.fill((255,0,0), (0,0,50,50))

    def run(self):
        """Displays stimulus and waits for stopping condition"""
        resp: Optional[str] = None
        rt: Optional[float] = None

        if self.paramsOK:
            self.draw_info = self.setup_visual_objects()
            self.star_time = timeit.default_timer()

            while True:
                resp = self.ready_to_stop()
                if resp:
                    rt = timeit.default_timer() - self.star_time
                    break

                self.draw_visual_objects()

                pygame.display.flip()
        else:
            log.error(f"oops, invalid parameters: {self.params}")

        return resp, rt


class TextTrialEvent(TrialEvent):
    """Subclass of TrialEvent for displaying text stimuli.
    params dict:
        message = text to display [REQUIRED]
        color = font color
        backcolor = background color
        fontname = font name (use None for sys default)
        fontsize = font size in pt
        fontbold = True or False
        note: location is always center of screen
    """

    def validate_params(self):
        # big problems
        if not self.surface:
            log.error("oops, you need to give me a valid pygame surface")
            return False
        if not self.params:
            log.error("oops, you need to specify a param dictionary")
            return False
        if "message" not in self.params:
            log.error("oops, params needs a key called 'message'")
            return False

        # little problems
        if "fontcolor" in self.params:
            self.params["color"] = self.params["fontcolor"]
        if "color" not in self.params:
            self.params["color"] = (255, 255, 255)
        if "backcolor" not in self.params:
            self.params["backcolor"] = (0, 0, 0)
        # Todo: This works in pycharm, but crashes after frozen (folder or .app), solution is to specify the fontname, e.g., 'Arial'
        if "fontname" not in self.params:
            self.params["fontname"] = None
        if "fontsize" not in self.params:
            self.params["fontsize"] = 24
        if "fontbold" not in self.params:
            self.params["fontbold"] = False

        return True

    def setup_visual_objects(self):
        my_font = pygame.font.SysFont(self.params["fontname"], self.params["fontsize"], self.params["fontbold"])
        my_text = my_font.render(self.params["message"], True, self.params["color"])
        win_height = self.surface.get_height()
        win_width = self.surface.get_width()
        msg_height = my_text.get_height()
        msg_width = my_text.get_width()
        msg_location = win_width // 2 - msg_width // 2, win_height // 2 - msg_height // 2

        return {"font": my_font, "text": my_text, "location": msg_location}

    def draw_visual_objects(self):
        self.surface.fill(self.params["backcolor"])
        self.surface.blit(self.draw_info["text"], self.draw_info["location"])


class MultilineTextTrialEvent(TrialEvent):
    """Subclass of TrialEvent for displaying text stimuli.
    params dict:
        message = text to display [REQUIRED]
        color = font color
        backcolor = background color
        fontname = font name (use None for sys default)
        fontsize = font size in pt
        fontbold = True or False
        note: location is always center of screen
    """

    def validate_params(self):
        # big problems
        if not self.surface:
            log.error("oops, you need to give me a valid pygame surface")
            return False
        if not self.params:
            log.error("oops, you need to specify a param dictionary")
            return False
        if "message" not in self.params:
            log.error("oops, params needs a key called 'message'")
            return False

        # little problems
        if "fontcolor" in self.params:
            self.params["color"] = self.params["fontcolor"]
        if "color" not in self.params:
            self.params["color"] = (255, 255, 255)
        if "backcolor" not in self.params:
            self.params["backcolor"] = (0, 0, 0)
        if "fontname" not in self.params:
            self.params["fontname"] = None
        if "fontsize" not in self.params:
            self.params["fontsize"] = 24
        if "fontbold" not in self.params:
            self.params["fontbold"] = False

        return True

    def setup_visual_objects(self):
        win_height = self.surface.get_height()
        win_width = self.surface.get_width()
        msg_list = self.params["message"].split("\n")
        text_obj_list = []
        h_list = []
        # create all the msg objects
        for i, a_msg in enumerate(msg_list):
            my_font = pygame.font.SysFont(self.params["fontname"], self.params["fontsize"], self.params["fontbold"])
            my_text = my_font.render(a_msg, True, self.params["color"])
            msg_height = my_text.get_height()
            # msg_width = my_text.get_width()
            h_list.append(msg_height)
            # msg_location = win_width // 2 - msg_width // 2, win_height // 2 - msg_height // 2
            # text_obj_list.append({"font": my_font, "text": my_text, "location": msg_location})
            text_obj_list.append({"font": my_font, "text": my_text})
        # center them
        max_h = max(h_list)
        sum_h = sum(h_list)
        upper_y = win_height // 2 - sum_h // 2
        for y, txt_obj in enumerate(text_obj_list):
            txt_obj["location"] = (win_width // 2 - txt_obj["text"].get_width() // 2, upper_y + max_h * y)
        return text_obj_list

    def draw_visual_objects(self):
        self.surface.fill(self.params["backcolor"])
        for txt_obj in self.draw_info:
            self.surface.blit(txt_obj["text"], txt_obj["location"])


class CircleTrialEvent(TrialEvent):
    """Subclass of TrialEvent for displaying circle stimuli
    params dict:
        color = circle color
        backcolor = background color
        radius = circle radius
        location = circle location (x,y)
                   (make either value None to center on axis)
    """

    def validate_params(self):
        # Fail on critical errors
        if not self.surface:
            log.error(f"Error: Invalid pygame surface: {self.surface}")
            return False

        # Defaults for other missing parameters
        if "color" not in self.params:
            self.params["color"] = (255, 255, 255)
        if "backcolor" not in self.params:
            self.params["backcolor"] = (0, 0, 0)
        if "radius" not in self.params:
            self.params["radius"] = 50
        if "location" not in self.params:
            self.params["location"] = (None, None)
        if "offset" not in self.params:
            self.params["offset"] = 0

        # if you get here, everything is ok
        return True

    def setup_visual_objects(self):
        # compute centered location
        win_width = self.surface.get_width()
        win_height = self.surface.get_height()

        x, y = self.params["location"]
        if not x:
            x = win_width // 2
        if not y:
            y = win_height // 2
        x += self.params["offset"]
        circle_position = x, y

        return {"position": circle_position}

    def draw_visual_objects(self):
        self.surface.fill(self.params["backcolor"])
        # draw a filled circle on the main surface
        pygame.draw.circle(self.surface, self.params["color"], self.draw_info["position"], self.params["radius"])
        return


class PictureTrialEvent(TrialEvent):
    """Subclass of TrialEvent for displaying picture stimuli
    params dict:
        backcolor = background color
        picfile = picture filename
        location = circle location (x,y)
                   (make either value None to center on axis)
    """

    def validate_params(self):
        # Fail on critical errors
        if not self.surface:
            log.error(f"Error: Invalid pygame surface: {self.surface}")
            return False
        if "picfile" not in self.params:
            log.error("Error: PictureTrialEvent requires a 'picfile' parameter, but none was given.")
            return False
        if "picfile" in self.params and not os.path.isfile(self.params["picfile"]):
            log.error(
                f"""Error: PictureTrialEvent initialized with invalid 'picfile' parameter: {self.params["picfile"]}"""
            )
            return False

        # Defaults for other missing parameters
        if "backcolor" not in self.params:
            self.params["backcolor"] = (0, 0, 0)
        if "location" not in self.params:
            self.params["location"] = (None, None)
        if "fullscreen" not in self.params:
            self.params["fullscreen"] = False

        # if you get here, everything is ok
        return True

    def setup_visual_objects(self):
        # compute centered location
        win_width = self.surface.get_width()
        win_height = self.surface.get_height()

        the_picture = pygame.image.load(self.params["picfile"])

        if self.params["fullscreen"]:
            try:
                the_picture = pygame.transform.scale(the_picture, (win_width, win_height))
            except Exception as e:
                log.error(f"Error: Unable to scale {self.params['picfile']} to fullscreen:\n{e}")

        pic_w = the_picture.get_width()
        pic_h = the_picture.get_height()

        x, y = self.params["location"]
        if not x:
            x = win_width // 2 - pic_w // 2
        if not y:
            y = win_height // 2 - pic_h // 2
        picture_position = x, y

        return {"image": the_picture, "position": picture_position}

    def draw_visual_objects(self):
        self.surface.fill(self.params["backcolor"])
        # BLIT (draw) the picture data on the main window
        self.surface.blit(self.draw_info["image"], self.draw_info["position"])
        return


if __name__ == "__main__":
    pygame.init()

    main_surface = pygame.display.set_mode((1024, 768))

    # # *** Test The Base Class (altered to show red rect on default black background)
    # my_trial_event = TrialEvent(surface=main_surface,
    #                           params={},
    #                           stopinfo={'keypress':['a', 'b'],
    #                                     'timelimit': 6}
    #                           )
    # log.error (f"base class response {my_trial_event.run()}")

    # *** Test The Text Class
    my_trial_event = TextTrialEvent(
        surface=main_surface,
        params={"message": "Hi There, This is a singleline Text Object", "fontsize": 40, "fontname": "Courier"},
        stopinfo={"keypress": ["a", "b"], "timelimit": 6},
    )
    log.info("text stimulus response = {my_trial_event.run()}")

    # *** Test The Multiline Text Class
    my_trial_event = MultilineTextTrialEvent(
        surface=main_surface,
        params={
            "message": "Hi There\nThis is\nA multiline test example\ntest\n\n\n\n\n\n\n\nPress Spacebar To Continue",
            "fontsize": 40,
            "fontname": "Courier",
        },
        stopinfo={"keypress": ["a", "b"], "timelimit": 10},
    )
    log.info(f"multiline text stimulus response = {my_trial_event.run()}")

    # *** Test The Circle Class
    my_trial_event = CircleTrialEvent(
        surface=main_surface,
        params={"color": (0, 255, 0), "backcolor": (0, 100, 100)},
        stopinfo={"keypress": ["a", "b"], "timelimit": 6},
    )
    response = my_trial_event.run()
    log.info(f"circle response = {response}")

    # *** Test The Picture Class
    my_trial_event = PictureTrialEvent(
        surface=main_surface,
        params={"picfile": "r2d2_small.png", "location": (None, None)},
        stopinfo={"keypress": ["a", "b"], "timelimit": 6},
    )
    response = my_trial_event.run()
    log.info(f"picture response = {response}")

    pygame.quit()
