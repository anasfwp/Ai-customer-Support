import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Mail, Lock, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { errorMessage, sessionNotice } from '../api/client';

export default function LoginPage() {
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [sessionExpired] = useState(() => sessionNotice.consumeExpired());
  const [slow, setSlow] = useState(false);

  // The free Render backend sleeps when idle; the first request can take a
  // while, so tell the user it is waking up instead of leaving a bare spinner.
  useEffect(() => {
    if (!isLoading) {
      setSlow(false);
      return;
    }
    const timer = setTimeout(() => setSlow(true), 5000);
    return () => clearTimeout(timer);
  }, [isLoading]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please enter your email and password');
      return;
    }

    try {
      await login(email, password);
      toast.success('Welcome back!');
      navigate('/chat');
    } catch (err) {
      const message = errorMessage(err, 'Invalid email or password');
      setError(message);
      toast.error(message);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left panel: branding */}
      <div className="relative hidden w-1/2 overflow-hidden bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-700 lg:block">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.15),transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(255,255,255,0.1),transparent_50%)]" />

        <div className="relative flex h-full flex-col justify-between p-12 text-white">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
              <Sparkles className="h-5 w-5" />
            </div>
            <span className="text-lg font-semibold">AI Support Assistant</span>
          </div>

          <div>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-4xl font-bold leading-tight lg:text-5xl"
            >
              Answers in seconds,
              <br />
              grounded in your docs.
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="mt-4 max-w-md text-lg text-white/80"
            >
              Upload your documents once, then ask anything. Get cited answers pulled straight from your knowledge base.
            </motion.p>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mt-8 flex items-center gap-6 text-sm text-white/70"
            >
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-emerald-400" />
                Cited sources
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-emerald-400" />
                Multi-tenant
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-emerald-400" />
                RAG powered
              </div>
            </motion.div>
          </div>

          <p className="text-xs text-white/60">
            © 2026 AI Support Assistant. All rights reserved.
          </p>
        </div>
      </div>

      {/* Right panel: form */}
      <div className="flex w-full items-center justify-center bg-slate-50 p-6 dark:bg-slate-950 lg:w-1/2">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-md"
        >
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              AI Support Assistant
            </span>
          </div>

          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Welcome back
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Sign in to your account to continue
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-[38px] h-4 w-4 text-slate-400" />
              <Input
                label="Email"
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-9"
                autoComplete="email"
                autoFocus
              />
            </div>

            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-[38px] h-4 w-4 text-slate-400" />
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-9"
                autoComplete="current-password"
              />
            </div>

            {sessionExpired && !error && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-300">
                Your session expired. Please sign in again.
              </div>
            )}

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
                {error}
              </div>
            )}

            <Button type="submit" size="lg" fullWidth loading={isLoading}>
              Sign in
              {!isLoading && <ArrowRight className="h-4 w-4" />}
            </Button>

            {slow && (
              <p className="text-center text-xs text-slate-500 dark:text-slate-400">
                The server is waking up, this can take up to a minute…
              </p>
            )}
          </form>

          <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            Don&apos;t have an account?{' '}
            <Link
              to="/register"
              className="font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              Create one
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}