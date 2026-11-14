import { useQuery } from "@tanstack/react-query";
import { authApi } from "../api/auth-api";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["current-user"],
    queryFn: authApi.getCurrentUser,
    staleTime: 1000 * 60 * 5,
    retry: 1,
  });
}
