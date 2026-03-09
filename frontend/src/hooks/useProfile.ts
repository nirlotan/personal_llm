// useProfile – manages category and account selection state.
"use client";

import { useCallback, useState } from "react";
import { getAccountsForCategory, getCategories, submitProfile } from "@/lib/api";
import type { Account } from "@/lib/types";
import { MAX_CATEGORIES, MIN_CATEGORIES, MIN_ACCOUNTS_PER_CATEGORY, MAX_ACCOUNTS_PER_CATEGORY } from "@/lib/constants";

export function useProfile(sessionId: string | undefined) {
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [categoriesConfirmed, setCategoriesConfirmed] = useState(false);

  // Per-category accounts
  const [currentCategoryIndex, setCurrentCategoryIndex] = useState(0);
  const [categoryAccounts, setCategoryAccounts] = useState<Account[]>([]);
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [allSelectedAccounts, setAllSelectedAccounts] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCategories = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getCategories();
      setCategories(res.categories);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load categories");
    } finally {
      setLoading(false);
    }
  }, []);

  const toggleCategory = useCallback(
    (cat: string) => {
      setSelectedCategories((prev) => {
        if (prev.includes(cat)) return prev.filter((c) => c !== cat);
        if (prev.length >= MAX_CATEGORIES) return prev;
        return [...prev, cat];
      });
    },
    []
  );

  const confirmCategories = useCallback(() => {
    if (selectedCategories.length >= MIN_CATEGORIES && selectedCategories.length <= MAX_CATEGORIES) {
      setCategoriesConfirmed(true);
      setCurrentCategoryIndex(0);
      setAllSelectedAccounts([]);
    }
  }, [selectedCategories]);

  const loadAccountsForCurrentCategory = useCallback(async () => {
    if (!selectedCategories[currentCategoryIndex]) return;
    setLoading(true);
    setSelectedAccounts([]);
    try {
      const res = await getAccountsForCategory(selectedCategories[currentCategoryIndex]);
      setCategoryAccounts(res.accounts);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load accounts");
    } finally {
      setLoading(false);
    }
  }, [currentCategoryIndex, selectedCategories]);

  const toggleAccount = useCallback((name: string) => {
    setSelectedAccounts((prev) => {
      if (prev.includes(name)) return prev.filter((a) => a !== name);
      if (prev.length >= MAX_ACCOUNTS_PER_CATEGORY) return prev;
      return [...prev, name];
    });
  }, []);

  const canProceedAccounts =
    selectedAccounts.length >= MIN_ACCOUNTS_PER_CATEGORY &&
    selectedAccounts.length <= MAX_ACCOUNTS_PER_CATEGORY;

  const nextCategory = useCallback(() => {
    setAllSelectedAccounts((prev) => [...prev, ...selectedAccounts]);
    if (currentCategoryIndex < selectedCategories.length - 1) {
      setCurrentCategoryIndex((i) => i + 1);
    }
  }, [currentCategoryIndex, selectedAccounts, selectedCategories.length]);

  const isLastCategory = currentCategoryIndex === selectedCategories.length - 1;

  const submitUserProfile = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    const finalAccounts = [...allSelectedAccounts, ...selectedAccounts];
    try {
      await submitProfile(sessionId, {
        selected_categories: selectedCategories,
        selected_accounts: finalAccounts,
      });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to submit profile");
      throw e;
    } finally {
      setLoading(false);
    }
  }, [sessionId, allSelectedAccounts, selectedAccounts, selectedCategories]);

  const resetToCategories = useCallback(() => {
    setCategoriesConfirmed(false);
    setSelectedCategories([]);
    setCurrentCategoryIndex(0);
    setAllSelectedAccounts([]);
    setSelectedAccounts([]);
  }, []);

  return {
    categories,
    selectedCategories,
    categoriesConfirmed,
    categoryAccounts,
    selectedAccounts,
    currentCategoryIndex,
    currentCategory: selectedCategories[currentCategoryIndex] ?? "",
    loading,
    error,
    canProceedCategories:
      selectedCategories.length >= MIN_CATEGORIES &&
      selectedCategories.length <= MAX_CATEGORIES,
    canProceedAccounts,
    isLastCategory,
    loadCategories,
    toggleCategory,
    confirmCategories,
    loadAccountsForCurrentCategory,
    toggleAccount,
    nextCategory,
    submitUserProfile,
    resetToCategories,
  };
}
