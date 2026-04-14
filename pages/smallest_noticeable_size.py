import math
import random

import streamlit as st

from utils.test_config import load_test_config
from utils.ui import (
    render_instructions,
    render_page_header,
)

st.set_page_config(
    page_title="Visual Resolution (Tumbling E Staircase)",
    layout="wide",
)

render_page_header(
    "Visual Resolution Test (Tumbling E Staircase)",
    "Single-optotype adaptive staircase with error logging and MAR tracking.",
    "size",
)

render_instructions(
    "How To Run This Test",
    (
        "You will see one Tumbling E at a time. Choose its orientation. "
        "Correct responses make the next E smaller; incorrect responses make it larger. "
        "The smallest rendered optotype is 4 px, so if that remains easy, increase "
        "viewing distance."
    ),
    [
        "Keep viewing distance fixed during the run.",
        "Answer every trial with one of: Up, Down, Left, Right.",
        "If the smallest E is still obvious, move farther from the display and restart.",
    ],
)

config = load_test_config()
cfg = config["tumbling_e"]
SIZE_LEVELS_PX = [int(v) for v in cfg["size_levels_px"]]
ORIENTATIONS = ["Up", "Down", "Left", "Right"]


def student_next_size_index(*, current_index: int, is_correct: bool, max_index: int) -> int:
    """Compute the next adaptive size index for the staircase.

    Why this function exists:
        This is the core adaptive rule for the visual acuity task. The page calls it
        after every response to decide whether the next Tumbling E should be harder
        (smaller) or easier (larger). If this logic is wrong, the whole test becomes
        invalid because stimulus difficulty no longer tracks performance.

    Inputs:
        current_index: Current index in `SIZE_LEVELS_PX`.
        is_correct: Whether the student selected the correct orientation this trial.
        max_index: Largest valid index in the size-level list.

    Output:
        The next valid index (integer) in the closed range `[0, max_index]`.

    Required behavior:
        - Correct response: move to a smaller optotype by increasing index by 1.
        - Incorrect response: move to a larger optotype by decreasing index by 1.
        - Always clamp so index never goes below 0 or above `max_index`.
    """
    if is_correct:
        next_index = current_index + 1
    else:
        next_index = current_index - 1
    next_index = max(0, min(next_index, max_index))
    return next_index


def student_build_trial_log_row(
    *,
    trial_no: int,
    size_px: int,
    mar_arcmin: float,
    correct_orientation: str,
    response: str,
) -> dict[str, str | int | float]:
    """Build a complete, standardized row for the trial log table.

    Why this function exists:
        The experiment needs a clean row per trial for grading and analysis. This
        function converts raw trial values into the exact display schema used later
        by `st.dataframe`, so every row is consistent and easy to interpret.

    Inputs:
        trial_no: 1-based trial counter.
        size_px: Rendered optotype size (pixels) for this trial.
        mar_arcmin: Calculated MAR value for this size and setup.
        correct_orientation: Ground-truth direction shown to the participant.
        response: Participant-selected direction.

    Output:
        Dictionary with the exact table columns expected by this page, including a
        correctness field derived from `response == correct_orientation`.

    Required behavior:
        - Keep column names consistent with existing table rendering.
        - Include correctness as an explicit readable value.
        - Round MAR to 2 decimals for stable, readable output.
    """
    is_correct = response == correct_orientation
    return {
        "Trial": trial_no,
        "Size (px)": size_px,
        "MAR (arcmin)": round(mar_arcmin, 2),
        "Correct Orientation": correct_orientation,
        "Your Response": response,
        "Correct": "Yes" if is_correct else "No",
    }


def student_validate_screen_geometry(
    *, distance_cm: float, screen_width_mm: float, screen_width_px: int
) -> bool:
    """Validate whether screen-geometry inputs are usable.

    Why this function exists:
        MAR calculations rely on physically meaningful geometry values. Invalid
        distances or screen dimensions create nonsense results and confuse users.

    Inputs:
        distance_cm: Viewing distance in centimeters.
        screen_width_mm: Physical display width in millimeters.
        screen_width_px: Horizontal pixel resolution corresponding to width.

    Output:
        `True` when values are valid for computation; otherwise `False`.

    Suggested checks:
        - All values are positive.
        - Pixel width is large enough to avoid divide-by-zero / tiny denominator.
        - Distance and width remain in realistic human-testing ranges.
    """
    if distance_cm <= 0 or screen_width_mm <= 0 or screen_width_px <= 0:
        return False
    if screen_width_px < 10:  # Arbitrary threshold to prevent tiny pixel pitch
        return False
    if distance_cm < 10 or distance_cm > 1000:  # 10 cm to 10 m range for typical testing
        return False
    # assuming personal monitor and not billboard display
    if screen_width_mm < 50 or screen_width_mm > 2000:  # 5 cm to 2 m range for typical displays
        return False  
    return True


def student_compute_mar_arcmin(size_px: int, mm_per_px: float, distance_cm: float) -> float:
    """Compute MAR (minimum angle of resolution) in arcminutes.

    Why this function exists:
        Pixel size alone is device-dependent; MAR converts that size into a vision
        metric that is comparable across screens and viewing distances.

    Inputs:
        size_px: Current optotype size in pixels.
        mm_per_px: Pixel pitch (millimeters per pixel).
        distance_cm: Viewing distance in centimeters.

    Output:
        MAR in arcminutes as a float.

    Implementation guidance:
        - Convert pixel size to millimeters (`size_px * mm_per_px`).
        - Convert distance to matching units (millimeters).
        - Use a small-angle geometry formula, then convert radians to arcminutes.
        - Return a positive float and guard invalid denominators.
    """
    size_mm = size_px * mm_per_px
    distance_mm = distance_cm * 10
    if distance_mm <= 0:
        raise ValueError("Distance must be positive and non-zero.")
    # approximate using ratio of thickness to distance 
    # (since distance >> thickness, angle is small)
    mar_radians = size_mm / distance_mm
    mar_arcmin = math.degrees(mar_radians) * 60
    return mar_arcmin


def student_format_trial_log_row(
    *,
    trial_no: int,
    size_px: int,
    mar_arcmin: float,
    correct_orientation: str,
    response: str,
) -> dict[str, str | int | float]:
    """Wrapper/formatter for a standardized trial-log row.

    Why this function exists:
        In many real codebases, one helper computes values and another helper
        formats them for display. Keeping this function separate teaches modular
        design and avoids spreading table-format logic across the page.

    Expected use:
        This function should return the same schema as `student_build_trial_log_row`,
        potentially by calling it internally and applying final formatting rules.
    """
    return student_build_trial_log_row(
        trial_no=trial_no,
        size_px=size_px,
        mar_arcmin=mar_arcmin,
        correct_orientation=correct_orientation,
        response=response,
    )


# with st.expander("Assignment TODOs (Edit This Page)"):
#     st.markdown(
#         "- Keep existing table column names."
#     )

# st.caption(
#     "How these functions connect: validate screen geometry -> convert size to MAR -> "
#     "log each trial consistently -> update index for next adaptive trial."
# )

try:
    _ = student_next_size_index(current_index=0, is_correct=True, max_index=len(SIZE_LEVELS_PX) - 1)
    _ = student_build_trial_log_row(
        trial_no=1,
        size_px=SIZE_LEVELS_PX[0],
        mar_arcmin=1.0,
        correct_orientation="Up",
        response="Up",
    )
except NotImplementedError as error:
    st.error(str(error))
    st.info("This page is locked until the student TODO functions are implemented.")
    st.stop()

if not student_validate_screen_geometry(
    distance_cm=float(cfg["setup"]["distance_cm"]["default"]),
    screen_width_mm=float(cfg["setup"]["screen_width_mm"]["default"]),
    screen_width_px=int(cfg["setup"]["screen_width_px"]["default"]),
):
    st.error("Geometry validation function returned invalid result.")
    st.stop()


def init_tumbling_state() -> dict:
    key = "tumbling_e_state"
    if key not in st.session_state:
        st.session_state[key] = {
            "size_index": 0,
            "trial_orientation": random.choice(ORIENTATIONS),
            "history": [],
        }
    return st.session_state[key]


def next_orientation(previous: str) -> str:
    candidate = random.choice(ORIENTATIONS)
    while candidate == previous:
        candidate = random.choice(ORIENTATIONS)
    return candidate


def e_symbol(size_px: int, orientation: str) -> str:
    rotation = {"Right": 0, "Down": 90, "Left": 180, "Up": 270}[orientation]
    return (
        "<div style='display:flex; justify-content:center; align-items:center; "
        "background:#ffffff; border:1px solid #d0d0d0; border-radius:8px; padding:0.3rem;'>"
        # LAB NOTE: SVG geometry enforces t=d (stroke thickness equals spacing) on a 5x5 grid.
        f"<svg width='{size_px}' height='{size_px}' viewBox='0 0 5 5' "
        "xmlns='http://www.w3.org/2000/svg' style='display:block; shape-rendering:crispEdges;'>"
        f"<g transform='rotate({rotation} 2.5 2.5)' fill='#101010'>"
        "<rect x='0' y='0' width='1' height='5'/>"
        "<rect x='0' y='0' width='5' height='1'/>"
        "<rect x='0' y='2' width='5' height='1'/>"
        "<rect x='0' y='4' width='5' height='1'/>"
        "</g></svg></div>"
    )


with st.container(border=True):
    st.subheader("Test Setup")
    col_1, col_2, col_3 = st.columns(3)
    distance_cm = col_1.number_input(
        "Viewing distance (cm)",
        min_value=float(cfg["setup"]["distance_cm"]["min"]),
        max_value=float(cfg["setup"]["distance_cm"]["max"]),
        value=float(cfg["setup"]["distance_cm"]["default"]),
        step=float(cfg["setup"]["distance_cm"]["step"]),
    )
    screen_width_mm = col_2.number_input(
        "Screen width (mm)",
        min_value=float(cfg["setup"]["screen_width_mm"]["min"]),
        max_value=float(cfg["setup"]["screen_width_mm"]["max"]),
        value=float(cfg["setup"]["screen_width_mm"]["default"]),
        step=float(cfg["setup"]["screen_width_mm"]["step"]),
    )
    screen_width_px = col_3.number_input(
        "Screen width (pixels)",
        min_value=int(cfg["setup"]["screen_width_px"]["min"]),
        max_value=int(cfg["setup"]["screen_width_px"]["max"]),
        value=int(cfg["setup"]["screen_width_px"]["default"]),
        step=int(cfg["setup"]["screen_width_px"]["step"]),
    )
    mm_per_px = float(screen_width_mm) / float(screen_width_px)
    st.caption(f"Pixel pitch: {mm_per_px:.4f} mm/px")
    st.caption(
        "Smallest E size in this app is 4 px. Increase viewing distance to push "
        "difficulty when needed."
    )


def mar_arcmin_for_size(size_px: int, mm_per_px: float, distance_cm: float) -> float:
    return student_compute_mar_arcmin(size_px=size_px, mm_per_px=mm_per_px, distance_cm=distance_cm)


state = init_tumbling_state()
feedback_key = "tumbling_e_last_feedback"
current_index = int(state["size_index"])
current_size_px = SIZE_LEVELS_PX[current_index]
current_orientation = state["trial_orientation"]
current_mar = mar_arcmin_for_size(current_size_px, mm_per_px, distance_cm)

with st.container(border=True):
    st.subheader("Adaptive Tumbling E Trial")
    st.caption(
        f"Current size: {current_size_px}px | Current MAR: {current_mar:.2f} arcmin"
    )
    st.markdown(e_symbol(current_size_px, current_orientation), unsafe_allow_html=True)

with st.container(border=True):
    st.subheader("Respond")
    last_feedback = st.session_state.get(feedback_key)
    if last_feedback == "correct":
        st.success("Previous response: Correct.")
    elif last_feedback == "incorrect":
        st.error("Previous response: Incorrect.")

    # Initialize listening state
    if "tumbling_listening" not in st.session_state:
        st.session_state["tumbling_listening"] = False
    
    # Clear keyboard input if flag is set (must happen BEFORE widget is created)
    if st.session_state.get("tumbling_clear_keyboard", False):
        st.session_state["tumbling_keyboard_input"] = ""
        st.session_state["tumbling_clear_keyboard"] = False
    
    # Initialize response (will be set if user provides input)
    response = None
    
    if not st.session_state["tumbling_listening"]:
        if st.button("🎹 Start - Enable Keyboard Input", use_container_width=True, type="primary"):
            st.session_state["tumbling_listening"] = True
            st.rerun()
    else:
        st.success("⌨️ Keyboard listening ACTIVE - Use WASD (W=Up, A=Left, S=Down, D=Right)")
        
        # Use the text input value to trigger responses
        keyboard_input = st.text_input(
            "Type WASD to respond:",
            key="tumbling_keyboard_input",
            placeholder="Type W/A/S/D here",
        )
        
        # If user typed something, process it immediately
        if keyboard_input:
            response_map = {
                'w': 'Up', 'W': 'Up',
                'a': 'Left', 'A': 'Left',
                's': 'Down', 'S': 'Down',
                'd': 'Right', 'D': 'Right',
            }
            # Get the last character entered
            last_char = keyboard_input[-1] if keyboard_input else None
            if last_char in response_map:
                response = response_map[last_char]
                # Set flag to clear on next render
                st.session_state["tumbling_clear_keyboard"] = True
        
        st.caption("Use arrow buttons or type WASD:")
        
        # Use columns for button layout
        col1, col2, col3, col4 = st.columns(4)
        
        up_clicked = col1.button("⬆️ Up", use_container_width=True)
        down_clicked = col2.button("⬇️ Down", use_container_width=True)
        left_clicked = col3.button("⬅️ Left", use_container_width=True)
        right_clicked = col4.button("➡️ Right", use_container_width=True)
        
        # Check button clicks (takes precedence over keyboard)
        if up_clicked:
            response = "Up"
        elif down_clicked:
            response = "Down"
        elif left_clicked:
            response = "Left"
        elif right_clicked:
            response = "Right"
    
    if response:
        is_correct = response == current_orientation
        state["history"].append(
            student_build_trial_log_row(
                trial_no=len(state["history"]) + 1,
                size_px=current_size_px,
                mar_arcmin=current_mar,
                correct_orientation=current_orientation,
                response=response,
            )
        )

        next_index = student_next_size_index(
            current_index=current_index,
            is_correct=is_correct,
            max_index=len(SIZE_LEVELS_PX) - 1,
        )

        state["size_index"] = next_index
        state["trial_orientation"] = next_orientation(current_orientation)
        st.session_state[feedback_key] = "correct" if is_correct else "incorrect"
        st.session_state["tumbling_clear_keyboard"] = True  # Clear input on next render
        st.rerun()

with st.container(border=True):
    st.subheader("Trial Log")
    history = state["history"]
    if history:
        st.dataframe(history, width="stretch", hide_index=True)
        wrong_only = [row for row in history if row["Correct"] == "No"]
        st.markdown("**Incorrect Responses**")
        if wrong_only:
            st.dataframe(wrong_only, width="stretch", hide_index=True)
        else:
            st.caption("No incorrect responses yet.")
    else:
        st.caption("No responses yet.")

with st.container(border=True):
    st.subheader("Test Controls")
    if st.button("Restart Staircase", width="stretch"):
        st.session_state.pop("tumbling_e_state", None)
        st.session_state.pop(feedback_key, None)
        st.rerun()
