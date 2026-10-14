import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { canStartPageDrag, clampDrag, clampOffset, directionalDrag, isVerticalIntent, releaseIndex } from '../src/navigation/physics';

const height = 800;

describe('Intent and ownership of vertical universe gestures', () => {
  test('tiny movements, horizontal swipes and diagonals do not capture a page', () => {
    assert.equal(isVerticalIntent(0, 11), false);
    assert.equal(isVerticalIntent(0, -11), false);
    assert.equal(isVerticalIntent(30, 12), false);
    assert.equal(isVerticalIntent(30, -30), false);
    assert.equal(isVerticalIntent(-30, 30), false);
    assert.equal(isVerticalIntent(0, 12), true);
    assert.equal(isVerticalIntent(8, -20), true);
  });

  test('upward swipes from Home require its list to have started at the bottom', () => {
    assert.equal(canStartPageDrag(0, 2, -60, 0, 300), false);
    assert.equal(canStartPageDrag(0, 2, -60, 150, 300), false);
    assert.equal(canStartPageDrag(0, 2, -60, 300, 300), true);
    // Sub-pixel scroll measurement differences are allowed at the edge.
    assert.equal(canStartPageDrag(0, 2, -60, 299.5, 300), true);
    assert.equal(canStartPageDrag(0, 2, -60, 297, 300), false);
  });

  test('returning downward from Musculation requires the list to have started at the top', () => {
    assert.equal(canStartPageDrag(1, 2, 60, 0, 500), true);
    assert.equal(canStartPageDrag(1, 2, 60, 0.5, 500), true);
    assert.equal(canStartPageDrag(1, 2, 60, 3, 500), false);
    assert.equal(canStartPageDrag(1, 2, 60, 500, 500), false);
  });

  test('non-scrolling pages allow the adjacent universe while the outside bounds remain closed', () => {
    assert.equal(canStartPageDrag(0, 2, -60, 0, 0), true);
    assert.equal(canStartPageDrag(1, 2, 60, 0, 0), true);
    assert.equal(canStartPageDrag(0, 2, 60, 0, 0), false);
    assert.equal(canStartPageDrag(1, 2, -60, 0, 0), false);
    assert.equal(canStartPageDrag(0, 2, 0, 0, 0), false);
    assert.equal(canStartPageDrag(0, 1, -60, 0, 0), false);
  });

  test('a future third universe uses the same edge rules on the middle page', () => {
    assert.equal(canStartPageDrag(1, 3, 60, 0, 400), true);
    assert.equal(canStartPageDrag(1, 3, -60, 0, 400), false);
    assert.equal(canStartPageDrag(1, 3, 60, 400, 400), false);
    assert.equal(canStartPageDrag(1, 3, -60, 400, 400), true);
    assert.equal(canStartPageDrag(2, 3, -60, 0, 0), false);
    assert.equal(canStartPageDrag(2, 3, 60, 0, 400), true);
  });
});

describe('Following the finger and settling a universe', () => {
  test('track offsets cannot reveal space before Home or after the final universe', () => {
    assert.equal(clampOffset(40, height, 2), 0);
    assert.equal(clampOffset(-90, height, 2), -90);
    assert.equal(clampOffset(-height, height, 2), -height);
    assert.equal(clampOffset(-height * 2, height, 2), -height);
    assert.equal(clampOffset(-height * 3, height, 3), -height * 2);
    assert.ok(clampOffset(-100, 0, 2) === 0);
    assert.ok(clampOffset(-100, height, 1) === 0);
  });

  test('the interactive track follows displacement and is limited to the nearest adjacent page', () => {
    assert.equal(clampDrag(0, -80, height, 3), -80);
    assert.equal(clampDrag(1, 80, height, 3), -height + 80);
    assert.equal(clampDrag(1, -80, height, 3), -height - 80);
    assert.equal(clampDrag(0, -height * 4, height, 3), -height);
    assert.equal(clampDrag(1, -height * 4, height, 3), -height * 2);
    assert.equal(clampDrag(2, height * 4, height, 3), -height);
    assert.equal(clampDrag(0, 80, height, 3), 0);
    assert.equal(clampDrag(2, -80, height, 3), -height * 2);
  });

  test('backtracking can restore a page but cannot steal its opposite list boundary', () => {
    assert.equal(directionalDrag(-80, -1), -80);
    assert.equal(directionalDrag(80, 1), 80);
    assert.equal(directionalDrag(200, -1), 0);
    assert.equal(directionalDrag(-200, 1), 0);
    assert.equal(directionalDrag(0, -1), 0);
    assert.equal(directionalDrag(0, 1), 0);
    // The middle page started a downward gesture at the top of its list.
    // Reversing strongly upward can cancel, but cannot jump to future Cardio.
    const reverse = directionalDrag(-height, 1);
    assert.equal(clampDrag(1, reverse, height, 3), -height);
    assert.equal(releaseIndex(1, 3, reverse, -1500, height), 1);
  });

  test('a short drag returns to the same page even when its velocity has the opposite sign', () => {
    assert.equal(releaseIndex(0, 2, -80, -100, height), 0);
    assert.equal(releaseIndex(1, 2, 80, 100, height), 1);
    assert.equal(releaseIndex(0, 2, -80, 1000, height), 0);
    assert.equal(releaseIndex(1, 2, 80, -1000, height), 1);
    assert.equal(releaseIndex(0, 2, -11, -2000, height), 0);
  });

  test('a deliberate drag commits one page in either direction', () => {
    assert.equal(releaseIndex(0, 2, -height * 0.18, 0, height), 1);
    assert.equal(releaseIndex(1, 2, height * 0.18, 0, height), 0);
    assert.equal(releaseIndex(0, 2, -height * 0.17, 0, height), 0);
    assert.equal(releaseIndex(1, 2, height * 0.17, 0, height), 1);
  });

  test('a fast flick can complete a shorter drag only in the finger direction', () => {
    assert.equal(releaseIndex(0, 2, -40, -700, height), 1);
    assert.equal(releaseIndex(1, 2, 40, 700, height), 0);
    assert.equal(releaseIndex(0, 2, -40, -699, height), 0);
    assert.equal(releaseIndex(1, 2, 40, 699, height), 1);
  });

  test('long or fast swipes never skip a page or escape the first and last universe', () => {
    assert.equal(releaseIndex(0, 3, -height * 4, -5000, height), 1);
    assert.equal(releaseIndex(1, 3, -height * 4, -5000, height), 2);
    assert.equal(releaseIndex(2, 3, height * 4, 5000, height), 1);
    assert.equal(releaseIndex(0, 3, height, 5000, height), 0);
    assert.equal(releaseIndex(2, 3, -height, -5000, height), 2);
  });

  test('an unmeasured viewport and a one-page pager cannot change universe', () => {
    assert.equal(releaseIndex(0, 2, -300, -2000, 0), 0);
    assert.equal(releaseIndex(1, 2, 300, 2000, -1), 1);
    assert.equal(releaseIndex(0, 1, -height, -2000, height), 0);
    assert.equal(releaseIndex(0, 1, height, 2000, height), 0);
  });
});
