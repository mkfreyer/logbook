/** Keep a covered page at the viewport's top rather than sliding its footer in
 * from above. The track still owns the exact finger-following offset.
 * Effective page top = index * height + trackOffset + compensation
 *                    = max(0, index * height + trackOffset).
 * Higher-index opaque pages cover/reveal the earlier ones, without a gap.
 * This changes presentation only, never gesture recognition or release physics. */
export function coveredPageOffset(index: number, trackOffset: number, height: number): number {
  'worklet';
  return Math.max(0, -trackOffset - index * height);
}
