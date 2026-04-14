import streamlit as st

from utils.audio_tools import single_tone_wav
from utils.test_config import load_test_config
from utils.ui import (
    render_instructions,
    render_page_header,
)

st.set_page_config(
    page_title="Pitch Frequency Range Test",
    layout="wide",
)

render_page_header(
    "Pitch Frequency Range Test",
    "Use fine-grained controls to find your audible frequency range between 20 Hz and 20 kHz.",
    "pitch",
)

render_instructions(
    "How To Run This Test",
    (
        "Test tones from low to high frequencies with small frequency steps. Keep "
        "system volume fixed and use a quiet environment."
    ),
    [
        "Use the slider for quick sweeps and number input for exact frequencies.",
        "Increase frequency until you can no longer hear it reliably.",
        "Record the highest clearly audible frequency.",
    ],
)

config = load_test_config()
cfg = config["pitch_range"]


def format_frequency_hz(frequency_hz: int) -> str:
    """Format frequency as Hz under 1 kHz and kHz above 1 kHz."""
    if frequency_hz < 1000:
        return f"{frequency_hz} Hz"
    return f"{frequency_hz / 1000:.2f} kHz"


default_frequency = int(cfg["frequency_hz"]["default"])
default_amplitude = float(cfg["playback_amplitude"]["default"])


def student_estimate_audible_bounds(
    *,
    probe_history_hz: list[int],
    heard_flags: list[bool],
) -> tuple[int, int]:
    """Summarize heard probe frequencies into lower/upper bounds.

    Pair the frequencies marked as heard and return the min/max. If no probes
    were heard, return a sensible fallback such as the configured default.
    """
    crazy_high = 1000000000000000
    heard_max = 0
    heard_min = crazy_high
    for i in range(len(probe_history_hz)):
        if heard_flags[i]:
            heard_min = min(heard_min, probe_history_hz[i])
            heard_max = max(heard_max, probe_history_hz[i])
    if heard_max == 0:
        heard_max = default_frequency
    if heard_min == crazy_high:
        heard_min = default_frequency
    return heard_min, heard_max


def student_validate_audio_params(*, frequency_hz: int, amplitude: float) -> bool:
    """Ensure requested playback parameters stay within config limits.

    Return `True` when `frequency_hz` and `amplitude` fall inside the configured
    range, otherwise return `False`.
    """
    freq_min = int(cfg["frequency_hz"]["min"])
    freq_max = int(cfg["frequency_hz"]["max"])
    if frequency_hz < freq_min or frequency_hz > freq_max:
        return False
    amp_min = float(cfg["playback_amplitude"]["min"])
    amp_max = float(cfg["playback_amplitude"]["max"])
    if amplitude < amp_min or amplitude > amp_max:
        return False
    return True


# with st.expander("Assignment TODOs (Edit This Page)"):
#     st.markdown(
#         "- Implement `student_estimate_audible_bounds` using example probe results.\n"
#         "- Implement `student_validate_audio_params` to gate playback inputs."
#     )

# st.caption(
#     "Optional TODO: once the helper functions exist you could show estimated bounds "
#     "and validate that playback parameters stay within config limits."
# )

with st.container(border=True):
    st.subheader("Tone Playback")
    
    import math
    
    # Initialize synced frequency value in session_state
    if "frequency_hz_synced" not in st.session_state:
        st.session_state.frequency_hz_synced = default_frequency
    
    # Log slider - convert between log and linear scales
    min_hz = int(cfg["frequency_hz"]["min"])
    max_hz = int(cfg["frequency_hz"]["max"])
    log_min = math.log(min_hz)
    log_max = math.log(max_hz)
    log_current = math.log(st.session_state.frequency_hz_synced)
    
    log_slider_value = st.slider(
        f"Test frequency (Hz) - log scale ({min_hz}-{max_hz} Hz)",
        min_value=log_min,
        max_value=log_max,
        value=log_current,
        key="pitch_playback_slider",
        on_change=lambda: st.session_state.update(
            {"frequency_hz_synced": int(math.exp(st.session_state.pitch_playback_slider))}
        ),
    )
    st.caption(f"Current frequency: {int(st.session_state.frequency_hz_synced)} Hz")
    
    # Number input - updates synced value on change
    frequency_hz = st.number_input(
        "Exact test frequency (Hz)",
        min_value=int(cfg["frequency_hz"]["min"]),
        max_value=int(cfg["frequency_hz"]["max"]),
        value=st.session_state.frequency_hz_synced,
        step=int(cfg["frequency_hz"]["step"]),
        key="pitch_playback_input",
        on_change=lambda: st.session_state.update(
            {"frequency_hz_synced": st.session_state.pitch_playback_input}
        ),
    )
    
    # Use the synced value
    frequency_hz = st.session_state.frequency_hz_synced
    amplitude = st.slider(
        "Playback amplitude",
        min_value=float(cfg["playback_amplitude"]["min"]),
        max_value=float(cfg["playback_amplitude"]["max"]),
        value=default_amplitude,
        step=float(cfg["playback_amplitude"]["step"]),
    )
    st.audio(single_tone_wav(frequency_hz=frequency_hz, amplitude=amplitude), format="audio/wav")
    st.caption(f"Current test tone: {int(frequency_hz)} Hz")
