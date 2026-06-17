import { redirect } from 'next/navigation'

// Auth is disabled — anyone can access the dashboard directly.
export default function LoginPage() {
  redirect('/dashboard')
}
