import { useAuth } from "../context/AuthContext";
import { DELETE_ROLES, WRITE_ROLES } from "../utils/constants";

export function permissionsFor(role) {
  return { canWrite: WRITE_ROLES.includes(role), canDelete: DELETE_ROLES.includes(role) };
}

export default function usePermissions() {
  const { user } = useAuth();
  return permissionsFor(user?.role);
}
