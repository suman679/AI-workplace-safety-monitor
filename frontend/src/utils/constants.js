export const PPE_LABELS = {
  HELMET: "Helmet",
  VEST: "Safety Vest",
  GLOVES: "Gloves",
  SAFETY_SHOES: "Safety Shoes",
  MASK: "Face Mask",
};
export const PPE_ORDER = Object.keys(PPE_LABELS);

export const SITE_TYPES = [
  { value: "CONSTRUCTION", label: "Construction" },
  { value: "FACTORY", label: "Factory" },
  { value: "WAREHOUSE", label: "Warehouse" },
  { value: "OTHER", label: "Other" },
];

export const SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

export const SOURCE_TYPES = [
  { value: "WEBCAM", label: "Webcam" },
  { value: "VIDEO", label: "Uploaded video" },
  { value: "RTSP", label: "RTSP / CCTV (future)" },
];

export const CAMERA_STATUSES = ["ONLINE", "OFFLINE", "WARNING"];
export const STATUS_TONE = { ONLINE: "green", OFFLINE: "slate", WARNING: "amber" };

export const WRITE_ROLES = ["SUPER_ADMIN", "COMPANY_ADMIN", "SAFETY_MANAGER"];
export const DELETE_ROLES = ["SUPER_ADMIN", "COMPANY_ADMIN"];
