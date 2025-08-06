# Hibikidō Energy Model: Systematic Sound Classification

_Additive classification system for analyzing and categorizing sounds in the Hibikidō database_

## Philosophy

This model provides a systematic way to analyze and classify sounds based on their fundamental energy characteristics. Unlike traditional classifications that mix different levels of description, this system uses **independent, additive components** that can be objectively measured and combined to create precise energy profiles.

## Core Components

Each sound is analyzed across six independent dimensions:

### 1. Attack Behavior

_How energy begins_

**Sharp**: Instant attack

- **Definition**: Attack time < 5ms
- **Measurement**: Time from silence to 90% of peak amplitude
- **Examples**: Percussion hits, clicks, snaps, impacts

**Soft**: Gradual attack

- **Definition**: Attack time > 500ms
- **Measurement**: Time from silence to 90% of peak amplitude
- **Examples**: Bowed strings, breath sounds, fades, swells

### 2. Decay Behavior

_How energy transitions after attack_

**Quick**: Rapid energy drop

- **Definition**: Decay time < 100ms (from peak to -20dB)
- **Examples**: Dry percussion, snaps, clicks

**Slow**: Gradual energy drop

- **Definition**: Decay time > 2000ms (from peak to -20dB)
- **Examples**: Piano resonance, bells, reverb tails

**None**: No significant decay

- **Definition**: Amplitude remains > 80% of peak for entire duration
- **Examples**: Drones, held notes, continuous textures

### 3. Sustain Pattern

_What happens during the sustained portion_

**Static**: Steady energy level

- **Definition**: RMS variance < threshold during sustain portion
- **Examples**: Held notes, drones, constant textures

**Looping without decay**: Repeating patterns maintaining energy

- **Definition**: Periodic autocorrelation + stable RMS
- **Examples**: Perfect loops, cycling textures, steady oscillations

**Looping with decay**: Repeating patterns gradually diminishing

- **Definition**: Periodic autocorrelation + decreasing RMS
- **Examples**: Echoes, feedback, iterative decay patterns

### 4. Event Cardinality

_How many discrete events_

**Single**: One event

- **Definition**: One onset detected
- **Examples**: Single hit, one note, isolated sound

**Few**: 2-5 events (intuitively countable)

- **Definition**: 2-5 onsets detected
- **Examples**: A few drops, short sequence, brief phrase

**Many**: 6-20+ events (countable but requires attention)

- **Definition**: 6-20 onsets detected
- **Examples**: Rapid sequence, busy phrase, multiple impacts

**Dense**: Uncountable, grain-like masses

- **Definition**: >20 onsets OR onset density > threshold
- **Examples**: Granular textures, dense activity, noise-like materials

### 5. Temporal Behavior

_How events are distributed in time_

**Regular**: Steady, predictable timing

- **Definition**: Low variance in inter-onset intervals
- **Examples**: Metronome, steady pulse, clock ticking

**Accelerating**: Events get closer together over time

- **Definition**: Decreasing inter-onset intervals (negative slope)
- **Examples**: Rebond effects, accelerating sequences

**Decelerating**: Events get further apart over time

- **Definition**: Increasing inter-onset intervals (positive slope)
- **Examples**: Slowing sequences, ritardando effects

**Irregular**: Unpredictable, organic timing

- **Definition**: High variance in inter-onset intervals
- **Examples**: Natural rhythms, random events, organic patterns

### 6. Spectral Behavior

_How frequency content evolves_

**Static**: Fixed spectral content

- **Definition**: Low spectral centroid variance
- **Examples**: Pure tones, stable harmonics, fixed filtering

**Ascending**: Spectral content rises over time

- **Definition**: Positive spectral centroid slope
- **Examples**: Rising sweeps, ascending glissandos

**Descending**: Spectral content falls over time

- **Definition**: Negative spectral centroid slope
- **Examples**: Falling sweeps, descending glissandos, sirens

**Bidirectional**: Back-and-forth spectral movement

- **Definition**: Oscillating spectral centroid
- **Examples**: Trills, vibrato, spectral oscillation

**Expanding**: Spectral range widens over time

- **Definition**: Increasing spectral spread
- **Examples**: Opening filters, growing harmonics

**Contracting**: Spectral range narrows over time

- **Definition**: Decreasing spectral spread
- **Examples**: Closing filters, reducing harmonics

## Analysis Implementation

### Adaptive Analysis Strategy

**Step 1: Complexity Detection**

Determine if sound is **Simple** or **Complex**:

**Complexity Indicators**:

- **Onset density**: <2 onsets/second = Simple, >10 onsets/second = Complex
- **Spectral stability**: Low variance = Simple, high variance = Complex
- **Energy coherence**: Smooth envelope = Simple, chaotic = Complex
- **Harmonic consistency**: Stable harmonics = Simple, shifting = Complex

**Step 2: Analysis Mode**

**For Simple Sounds**:

- Analyze entire sound as single unit
- Report precise single values for each dimension
- High confidence ratings

**For Complex Sounds**:

- Use 500ms-1000ms analysis windows with 50% overlap
- Report statistical distributions for each dimension
- Medium confidence ratings

### Analysis Output Format

**Simple Sound Example** (Clean siren):

```json
{
  "complexity": "simple",
  "confidence": "high",
  "attack": "soft",
  "attack_time_ms": 1200,
  "decay": "none",
  "decay_time_ms": null,
  "sustain": "static",
  "cardinality": "single",
  "temporal": "n/a",
  "spectral": "descending",
  "spectral_slope": -0.8
}
```

**Complex Sound Example** (Train station):

```json
{
  "complexity": "complex",
  "confidence": "medium",
  "attack": {"sharp": 0.6, "soft": 0.3, "unclear": 0.1},
  "decay": {"quick": 0.4, "slow": 0.45, "none": 0.15},
  "sustain": {"static": 0.7, "looping": 0.2, "variable": 0.1},
  "cardinality": "dense",
  "average_onsets_per_window": 15,
  "temporal": {"irregular": 0.8, "regular": 0.2},
  "spectral": {"variable": 0.4, "static": 0.3, "ascending": 0.2, "descending": 0.1}
}
```

## Mapping to Vande Gorne's Energy Types

This additive system encompasses Vande Gorne's original classifications:

**Percussion-résonance** = Sharp attack + Slow decay + Static sustain + Single + (any temporal) + (any spectral)

**Rebond** = Sharp attack + Quick decay + Static sustain + Many + Accelerating + Static spectral

**Accumulation** = Sharp attack + Quick decay + Static sustain + Dense + (Regular/Irregular) + Variable spectral

**Flux** = Soft attack + None decay + Static sustain + (Single/continuous) + (n/a) + Static spectral

**Oscillation** = Sharp attack + Quick decay + Looping without decay + Many + Regular + Static spectral

**Balancement** = Soft attack + Slow decay + Looping with decay + Few + Irregular + Bidirectional spectral

**Frottement** = Soft attack + None decay + Looping without decay + Dense + Irregular + Variable spectral

**Pression-déformation** = Soft attack + None decay + Looping without decay + Single + (n/a) + Bidirectional spectral

## Technical Implementation Requirements

### Required Analysis Algorithms

1. **Onset Detection**: Spectral flux, complex domain, or machine learning approaches
2. **Amplitude Envelope**: RMS analysis with appropriate time constants
3. **Spectral Analysis**: STFT with centroid and spread calculations
4. **Autocorrelation**: For detecting periodic patterns in sustain portions
5. **Statistical Analysis**: Variance, slope calculation, distribution analysis

### Analysis Parameters

- **Frame size**: 1024-4096 samples (depending on sample rate)
- **Hop size**: 50% overlap for temporal resolution
- **Onset detection threshold**: Adaptive based on signal characteristics
- **Spectral analysis window**: Hamming or Blackman-Harris
- **Smoothing**: Apply appropriate smoothing for stable measurements

### Database Storage

Each sound file should store:

- **Energy profile**: Complete analysis results in JSON format
- **Confidence metrics**: How reliable each measurement is
- **Analysis metadata**: Version, parameters used, date analyzed
- **Manual overrides**: Allow manual correction of automatic analysis

## Usage for Natural Language Orchestration

This energy model enables:

1. **Semantic Mapping**: Natural language phrases map to energy component combinations
2. **Complementarity Rules**: Orchestrational intelligence can determine what energy types balance each other
3. **Sound Selection**: System can find sounds matching desired energy profiles
4. **Musical Coherence**: Ensure combinations make musical sense based on energy relationships

---

_This model provides the foundational classification system for Hibikidō's natural language orchestration, enabling systematic analysis and intelligent combination of sounds based on their fundamental energy characteristics._