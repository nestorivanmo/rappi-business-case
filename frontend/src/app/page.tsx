import { redirect } from "next/navigation";

export default function Home() {
  redirect("/dashboard?kam=ana-torres");
}
