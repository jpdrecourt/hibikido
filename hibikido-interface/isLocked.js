lockedState = 0;

// Outputs only if state changes
function isLocked() {
  if (this.patcher.locked) {
    if (lockedState == 0) {
      lockedState = 1;
      outlet(0, 1);
    }
  } else {
    if (lockedState == 1) {
      lockedState = 0;
      outlet(0, 0);
    }
  }
  // Otherwise don't return anything, no change in state
}

t = new Task(isLocked, this);
t.interval = 500; // Locked state polling interval

// Run only if activated
function msg_int(val) {
  if (val === 0) {
    t.cancel();
  } else {
    t.repeat();
  }
}
