"""Shared TODOs for all 3AFC assignment pages.

Why this file exists:
- All 3AFC pages use the same staircase, accuracy, and plotting patterns.
- Shared logic is implemented here once and reused by all 3AFC pages.

Used by:
- pages/sound_gap_detection.py
- pages/amplitude_threshold.py
- pages/pitch_threshold.py

Implementation expectations:
- Keep return types exactly as annotated.
- Prefer small, pure functions with no Streamlit state mutations.
- Validate/clamp values to avoid invalid outputs.
"""
import matplotlib.pyplot as plt

def shared_student_apply_reversal_update(
    *,
    current_level: float,
    step: float,
    is_correct: bool,
    correct_streak: int,
    down_n: int,
    min_level: float,
    max_level: float,
) -> tuple[float, int]:
    """Apply one 2-down/1-up staircase update.

    Inputs:
        current_level: current adaptive stimulus level.
        step: step size for level change.
        is_correct: whether the response is correct.
        correct_streak: consecutive correct count before this trial.
        down_n: number of correct responses needed to step down.
        min_level: minimum allowed level.
        max_level: maximum allowed level.

    Returns:
        Tuple `(next_level, next_correct_streak)` after one update.

    Safety requirements:
        - Clamp level to `[min_level, max_level]`.
        - Treat `down_n < 1` as 1 to avoid zero-step loops.
    """
    if not is_correct:
        next_level = min(current_level + step, max_level)
        next_correct_streak = 0
    else:
        next_correct_streak = correct_streak + 1
        if next_correct_streak >= max(down_n, 1):
            next_level = max(current_level - step, min_level)
            next_correct_streak = 0
        else:
            next_level = current_level
    return next_level, next_correct_streak


def shared_student_plot_staircase(
    history: list[dict], threshold: float, y_label: str, title: str
) -> None:
    """Plot the staircase trace for the given history.

    Expected plot content:
        - X-axis: trial number.
        - Y-axis: level value per trial.
        - Visual distinction for correct vs incorrect trials.
        - Threshold drawn as a horizontal dashed line.

    Safety requirements:
        - Do not crash for empty or very short history lists.
    """
    plt.figure(figsize=(10, 6))
    if history:
        levels = [entry["Level"] for entry in history]
        correctness = [entry["Correct"] for entry in history]
        plt.plot(levels, marker="o", linestyle="-")
        for i, (level, correct) in enumerate(zip(levels, correctness)):
            color = "green" if correct else "red"
            plt.scatter(i, level, color=color)
    plt.axhline(y=threshold, color="blue", linestyle="--", label="Threshold")
    plt.xlabel("Trial Number")
    plt.ylabel(y_label)
    plt.title(title)
    plt.legend(loc='best')
    plt.show()



def shared_student_build_three_interval_targets(*, target_index: int) -> list[bool]:
    """Build a length-3 target mask with exactly one `True` entry.

    Example:
        target_index=1 -> [False, True, False]
    """
    if target_index < 0 or target_index > 2:
        raise ValueError("target_index must be 0, 1, or 2.")
    return [i == target_index for i in range(3)]


def shared_student_update_staircase_state(
    *,
    current_level: float,
    step: float,
    is_correct: bool,
    correct_streak: int,
    down_n: int,
    min_level: float,
    max_level: float,
) -> tuple[float, int]:
    """Reusable helper that keeps staircase behavior consistent.

    This can wrap or share logic with `shared_student_apply_reversal_update`.
    """
    return shared_student_apply_reversal_update(
        current_level=current_level,
        step=step,
        is_correct=is_correct,
        correct_streak=correct_streak,
        down_n=down_n,
        min_level=min_level,
        max_level=max_level
    )


def shared_student_estimate_threshold_from_reversals(
    *, reversals: list[float], fallback_level: float, tail_count: int = 4
) -> float:
    """Estimate threshold using the trailing reversal points.

    Recommended behavior:
        - When there are enough reversals, average the last `tail_count` values.
        - Otherwise return `fallback_level`.
    """
    if len(reversals) >= 6:
        return sum(reversals[-tail_count:]) / tail_count
    else:
        return fallback_level


def shared_student_compute_recent_accuracy(history: list[dict], window: int = 12) -> float:
    """Compute a trailing percent-correct accuracy metric.

    Output should be a percentage in the `[0, 100]` range.
    """
    if not history:
        return 0.0
    if window < 1:
        raise ValueError("window must be at least 1.")
    recent_trials = history[-window:] if len(history) > window else history
    print(recent_trials)
    correct_count = sum(1 for trial in recent_trials if trial["Correct"])
    return (correct_count / len(recent_trials)) * 100


def shared_student_validate_audio_params(*, amplitude: float, stimulus_value: float) -> bool:
    """Validate amplitude and stimulus-specific numeric values.

    Returns:
        `True` when inputs are in safe ranges, otherwise `False`.
    """
    if amplitude < 0.0 or amplitude > 1.0:
        print("Amplitude out of range: must be between 0.0 and 1.0.")
        return False
    if stimulus_value < 0.0 or stimulus_value > 1.0:
        print("Stimulus value out of range: must be between 0.0 and 1.0.")
        return False
    return True


def shared_student_plot_staircase_with_threshold(
    *, history: list[dict], threshold: float, y_label: str, title: str
) -> None:
    """Wrapper that draws the staircase and highlights the threshold.

    Hint:
        Call `shared_student_plot_staircase(...)` internally to avoid duplicate code.
    """
    shared_student_plot_staircase(history=history, threshold=threshold, y_label=y_label, title=title)