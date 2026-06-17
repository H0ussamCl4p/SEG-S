// This project now uses Google Identity Services + FastAPI JWT
// for authentication. The legacy NextAuth API route is disabled
// to avoid conflicting /api/auth/* endpoints.

export const GET = () => {
	return new Response("NextAuth is disabled in this project.", {
		status: 404,
	})
}

export const POST = GET
