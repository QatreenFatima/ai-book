import React, { lazy, Suspense } from "react";
import { ChatProvider } from "@site/src/components/ChatProvider";

const ChatWidget = lazy(() => import("@site/src/components/ChatWidget"));

export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <ChatProvider>
      {children}
      <Suspense fallback={null}>
        <ChatWidget />
      </Suspense>
    </ChatProvider>
  );
}
