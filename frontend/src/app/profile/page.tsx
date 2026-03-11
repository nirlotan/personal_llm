// Profile page – interest & account selection (Step 1).
// Matches the glassmorphism design from new_design.html.
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import CategoryGrid from "@/components/profile/CategoryGrid";
import AccountPicker from "@/components/profile/AccountPicker";
import GradientButton from "@/components/ui/GradientButton";
import Dialog from "@/components/ui/Dialog";
import { useSession } from "@/hooks/useSession";
import { useProfile } from "@/hooks/useProfile";

export default function ProfilePage() {
  const router = useRouter();
  const { session, ready } = useSession();
  const profile = useProfile(session?.session_id);

  const [showCategoryDialog, setShowCategoryDialog] = useState(true);

  // Redirect if no session (wait until localStorage is read first)
  useEffect(() => {
    if (ready && !session) {
      router.push("/");
    }
  }, [ready, session, router]);

  // Load categories on mount
  useEffect(() => {
    profile.loadCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load accounts when entering account-selection phase
  useEffect(() => {
    if (profile.categoriesConfirmed) {
      profile.loadAccountsForCurrentCategory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile.categoriesConfirmed, profile.currentCategoryIndex]);

  const handleContinueCategories = () => {
    profile.confirmCategories();
  };

  const handleNextAccounts = async () => {
    if (profile.isLastCategory) {
      try {
        await profile.submitUserProfile();
        router.push("/chat");
      } catch {
        // Error is set in profile.error by the hook
      }
    } else {
      profile.nextCategory();
    }
  };

  if (!ready || !session) return null;

  return (
    <>
      <header className="text-center mb-10 w-full max-w-3xl">
        <h1 className="text-[32px] font-bold text-brand-dark mb-2 tracking-tight">
          {profile.categoriesConfirmed
            ? "Account Selection"
            : "Onboarding Interest Selection"}
        </h1>
        <p className="text-gray-600 text-base mb-6">
          {profile.categoriesConfirmed
            ? `Choose 3 to 5 accounts for "${profile.currentCategory}"`
            : "Select your interests to personalize your experience. Choose 3 to 5 topics."}
        </p>
        <div className="flex items-center justify-center gap-8">
          {!profile.categoriesConfirmed ? (
            <>
              <GradientButton variant="secondary" onClick={() => router.push("/")}>
                Back
              </GradientButton>
              <GradientButton
                onClick={handleContinueCategories}
                disabled={!profile.canProceedCategories}
              >
                Continue
              </GradientButton>
            </>
          ) : (
            <>
              <GradientButton variant="secondary" onClick={profile.resetToCategories}>
                Back
              </GradientButton>
              <GradientButton
                onClick={handleNextAccounts}
                disabled={!profile.canProceedAccounts || profile.loading}
              >
                {profile.isLastCategory ? "Start Chatting" : "Next"}
              </GradientButton>
            </>
          )}
        </div>
      </header>

      {/* Category dialog */}
      <Dialog
        open={showCategoryDialog && !profile.categoriesConfirmed}
        onClose={() => setShowCategoryDialog(false)}
        title="Categories Selection"
      >
        <p>Pick 3 to 5 topics that interest you most.</p>
        <p className="text-sm text-gray-500 mt-2">
          Next, you&apos;ll choose social media accounts related to those topics.
        </p>
      </Dialog>

      {/* Category selection phase */}
      {!profile.categoriesConfirmed && (
        <>
          <CategoryGrid
            categories={profile.categories}
            selected={profile.selectedCategories}
            onToggle={profile.toggleCategory}
          />

          {profile.selectedCategories.length > 5 && (
            <p className="text-red-500 text-sm mb-4">Select no more than 5 categories</p>
          )}

          <footer className="flex items-center justify-center gap-8 mt-4">
            <GradientButton variant="secondary" onClick={() => router.push("/")}>
              Back
            </GradientButton>
            <GradientButton
              onClick={handleContinueCategories}
              disabled={!profile.canProceedCategories}
            >
              Continue
            </GradientButton>
          </footer>
        </>
      )}

      {/* Account selection phase */}
      {profile.categoriesConfirmed && (
        <>
          <AccountPicker
            category={profile.currentCategory}
            accounts={profile.categoryAccounts}
            selected={profile.selectedAccounts}
            onToggle={profile.toggleAccount}
          />

          <footer className="flex items-center justify-center gap-8 mt-4">
            <GradientButton
              variant="secondary"
              onClick={profile.resetToCategories}
            >
              Back
            </GradientButton>
            <GradientButton
              onClick={handleNextAccounts}
              disabled={!profile.canProceedAccounts || profile.loading}
            >
              {profile.isLastCategory ? "Start Chatting" : "Next"}
            </GradientButton>
          </footer>
        </>
      )}
    </>
  );
}
