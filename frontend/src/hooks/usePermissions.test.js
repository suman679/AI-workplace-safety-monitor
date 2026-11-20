import { permissionsFor } from "./usePermissions";

test("viewers are read-only", () => {
  expect(permissionsFor("VIEWER")).toEqual({ canWrite: false, canDelete: false });
});

test("safety managers can write but not delete", () => {
  expect(permissionsFor("SAFETY_MANAGER")).toEqual({ canWrite: true, canDelete: false });
});

test("company admins can do both", () => {
  expect(permissionsFor("COMPANY_ADMIN")).toEqual({ canWrite: true, canDelete: true });
});
