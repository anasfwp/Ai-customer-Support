import { useState } from 'react';
import { Building2, Lock, Mail, Palette, Save, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import Layout from '../components/layout/Layout';
import TeamSection from '../components/settings/TeamSection';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { useAuth } from '../hooks/useAuth';
import { useDarkMode } from '../hooks/useDarkMode';

export default function SettingsPage() {
  const { user } = useAuth();
  const { isDark, toggle } = useDarkMode();

  const [primaryColor, setPrimaryColor] = useState('#6366f1');
  const [welcomeMessage, setWelcomeMessage] = useState(
    'Hi! Ask me anything about our documentation.',
  );

  const handleSaveBranding = () => {
    toast.success('Branding saved (placeholder)');
  };

  const handleDeleteAccount = () => {
    if (
      confirm(
        'Are you sure? This will permanently delete your account and all documents. This cannot be undone.',
      )
    ) {
      toast.error('Account deletion is disabled in this demo');
    }
  };

  return (
    <Layout title="Settings">
      <div className="mx-auto max-w-3xl space-y-8 px-4 py-6 sm:px-6 sm:py-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Settings
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Manage your account and workspace preferences.
          </p>
        </div>

        {/* Profile */}
        <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-500/10">
              <Mail className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Profile
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Your account information
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <Input label="Email" value={user?.email ?? ''} disabled />
            <Input
              label="Tenant ID"
              value={user?.tenantId ?? ''}
              disabled
              hint="Your workspace identifier"
            />
          </div>
        </section>

        {user?.isAdmin && <TeamSection />}

        {/* Password */}
        <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-50 dark:bg-amber-500/10">
              <Lock className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Password
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Change your account password
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <Input label="Current password" type="password" placeholder="••••••••" />
            <Input label="New password" type="password" placeholder="••••••••" />
            <Input label="Confirm new password" type="password" placeholder="••••••••" />
            <Button onClick={() => toast.success('Password change is coming soon')}>
              Update password
            </Button>
          </div>
        </section>

        {/* Branding */}
        <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 dark:bg-violet-500/10">
              <Palette className="h-4 w-4 text-violet-600 dark:text-violet-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Branding
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Customize your workspace appearance
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
                Primary color
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="h-10 w-16 cursor-pointer rounded-lg border border-slate-300 dark:border-slate-700"
                />
                <Input
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="max-w-[140px] font-mono text-xs"
                />
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
                Welcome message
              </label>
              <textarea
                value={welcomeMessage}
                onChange={(e) => setWelcomeMessage(e.target.value)}
                rows={3}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:ring-2 focus:ring-indigo-500/40 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              />
            </div>

            <div className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 px-3 py-2.5 dark:border-slate-800 dark:bg-slate-950">
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  Dark mode
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Toggle dark theme
                </p>
              </div>
              <button
                onClick={toggle}
                className={`relative h-6 w-11 rounded-full transition ${
                  isDark ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'
                }`}
                aria-label="Toggle dark mode"
              >
                <span
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition ${
                    isDark ? 'left-[22px]' : 'left-0.5'
                  }`}
                />
              </button>
            </div>

            <Button onClick={handleSaveBranding}>
              <Save className="h-4 w-4" />
              Save branding
            </Button>
          </div>
        </section>

        {/* Danger zone */}
        <section className="rounded-2xl border border-red-200 bg-red-50/50 p-6 dark:border-red-900/40 dark:bg-red-950/20">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-100 dark:bg-red-500/10">
              <Trash2 className="h-4 w-4 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-red-900 dark:text-red-300">
                Danger zone
              </h2>
              <p className="text-xs text-red-700/70 dark:text-red-400/70">
                Irreversible actions
              </p>
            </div>
          </div>

          <p className="mb-4 text-sm text-red-800 dark:text-red-300">
            Deleting your account will permanently remove all documents, chat history, and
            workspace data.
          </p>

          <Button variant="danger" onClick={handleDeleteAccount}>
            <Trash2 className="h-4 w-4" />
            Delete account
          </Button>
        </section>

        {/* Footer info */}
        <div className="flex items-center justify-center gap-2 text-xs text-slate-400 dark:text-slate-500">
          <Building2 className="h-3.5 w-3.5" />
          AI Support Assistant v0.1.0
        </div>
      </div>
    </Layout>
  );
}