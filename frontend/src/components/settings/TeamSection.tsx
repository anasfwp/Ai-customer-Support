import { useState, type FormEvent } from 'react';
import { ShieldCheck, UserPlus, Users } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Skeleton } from '../ui/Skeleton';
import { useTeam } from '../../hooks/useTeam';

const MIN_PASSWORD_LENGTH = 8;

/**
 * Admin-only: see who is in the company and add members, who can then be given access to restricted documents.
 */
export default function TeamSection() {
  const { members, isLoading, addMember, isAdding } = useTeam();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await addMember({ email, password, is_admin: isAdmin });
      setEmail('');
      setPassword('');
      setIsAdmin(false);
    } catch {
      /* toast already shown by the hook */
    }
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50 dark:bg-emerald-500/10">
          <Users className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Team</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Add people to your company so you can share restricted documents with them
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-100 dark:divide-slate-800 dark:border-slate-800">
          {members.map((m) => (
            <li key={m.id} className="flex items-center justify-between gap-3 px-3 py-2.5">
              <span className="truncate text-sm text-slate-700 dark:text-slate-200">{m.email}</span>
              {m.is_admin ? (
                <Badge variant="info">
                  <ShieldCheck className="h-3 w-3" />
                  Admin
                </Badge>
              ) : (
                <Badge>Member</Badge>
              )}
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleSubmit} className="mt-5 space-y-4 border-t border-slate-100 pt-5 dark:border-slate-800">
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Email"
            name="member-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="teammate@company.com"
          />
          <Input
            label="Temporary password"
            name="member-password"
            type="password"
            required
            minLength={MIN_PASSWORD_LENGTH}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            hint="Share it with them privately"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input
            type="checkbox"
            checked={isAdmin}
            onChange={(e) => setIsAdmin(e.target.checked)}
            className="accent-indigo-600"
          />
          Make admin (sees every document and analytics, can add members)
        </label>
        <Button type="submit" loading={isAdding}>
          <UserPlus className="h-4 w-4" />
          Add member
        </Button>
      </form>
    </section>
  );
}
