"use client";

import { Suspense } from "react";
import { Header } from "@/components/layout/header";
import { ChatView } from "@/components/chat/chat-view";
import { useKamSelector } from "@/hooks/use-kam-selector";

function DashboardContent() {
  const { currentKam } = useKamSelector();

  return <ChatView kam={currentKam} />;
}

export default function DashboardPage() {
  return (
    <div className="h-screen bg-white flex flex-col">
      <Suspense>
        <Header />
        <DashboardContent />
      </Suspense>
    </div>
  );
}
