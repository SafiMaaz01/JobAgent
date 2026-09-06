import { getProfile } from "@/lib/api";
import SettingsClient from "@/components/SettingsClient";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  let profile;
  try {
    profile = await getProfile();
  } catch (error) {
    return (
      <div className="error-banner">
        <div className="error-title">Failed to Load Profile</div>
        <div>
          {error instanceof Error ? error.message : "Could not connect to JobAgent API to load profile."}
        </div>
      </div>
    );
  }

  return <SettingsClient initialProfile={profile} />;
}
