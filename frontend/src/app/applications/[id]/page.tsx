import { notFound } from "next/navigation";
import { getApplicationDetail } from "@/lib/api";
import { ApplicationDetail } from "@/lib/types";
import ApplicationDetailClient from "@/components/ApplicationDetailClient";

export const dynamic = "force-dynamic";

interface ApplicationDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function ApplicationDetailPage({
  params,
}: ApplicationDetailPageProps) {
  const resolvedParams = await params;
  const jobId = parseInt(resolvedParams.id, 10);

  if (isNaN(jobId)) {
    notFound();
  }

  let app: ApplicationDetail;
  try {
    app = await getApplicationDetail(jobId);
  } catch {
    notFound();
  }

  return <ApplicationDetailClient initialApp={app} />;
}
