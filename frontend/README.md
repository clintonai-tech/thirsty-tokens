# Frontend

Next.js (App Router) + Tailwind + shadcn/ui. One page plus a methodology stub.

```
npm ci
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL to the Lambda function URL
npm run dev
npm test && npm run lint && npm run typecheck
```

`NEXT_PUBLIC_API_URL` is read at build time. Deploy on Vercel with root directory `frontend`.
