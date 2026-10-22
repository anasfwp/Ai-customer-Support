import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { usersApi } from '../api/users';
import { errorMessage } from '../api/client';

const TEAM_KEY = ['team'] as const;

export function useTeam(enabled = true) {
  const queryClient = useQueryClient();

  const listQuery = useQuery({
    queryKey: [...TEAM_KEY],
    queryFn: () => usersApi.list(),
    enabled,
  });

  const addMutation = useMutation({
    mutationFn: usersApi.add,
    onSuccess: (member) => {
      toast.success(`${member.email} added to your team`);
      queryClient.invalidateQueries({ queryKey: [...TEAM_KEY] });
    },
    onError: (error) => {
      toast.error(errorMessage(error, 'Failed to add team member'));
    },
  });

  return {
    members: listQuery.data ?? [],
    isLoading: listQuery.isLoading,
    addMember: addMutation.mutateAsync,
    isAdding: addMutation.isPending,
  };
}
