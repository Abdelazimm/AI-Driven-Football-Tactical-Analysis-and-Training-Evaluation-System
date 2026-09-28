/**
 * Canonical computer-vision methodology identifiers.
 *
 * MethodologyId describes WHICH detection/tracking pipeline processes a session.
 * This is separate from ApplicationMode, which describes HOW the application operates.
 */
export const METHODOLOGY_IDS = {
  METHOD_1_YOLO11_BOTSORT: 'METHOD_1_YOLO11_BOTSORT',
  METHOD_2_RFDETR_GTATRACK: 'METHOD_2_RFDETR_GTATRACK',
  METHOD_3_YOLO26_SRITRACK: 'METHOD_3_YOLO26_SRITRACK',
} as const;

export type MethodologyId = (typeof METHODOLOGY_IDS)[keyof typeof METHODOLOGY_IDS];

/**
 * Methodology operational readiness / availability.
 * Describes application readiness, NOT scientific ranking or accuracy.
 */
export const METHODOLOGY_AVAILABILITY = {
  AVAILABLE: 'AVAILABLE',
  UNAVAILABLE: 'UNAVAILABLE',
  EXPERIMENTAL: 'EXPERIMENTAL',
} as const;

export type MethodologyAvailability = (typeof METHODOLOGY_AVAILABILITY)[keyof typeof METHODOLOGY_AVAILABILITY];

