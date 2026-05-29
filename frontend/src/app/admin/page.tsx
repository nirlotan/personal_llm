// Admin screen – password-gated runtime settings panel.
"use client";

import { useState, useEffect } from "react";
import {
  adminLogin,
  adminGetOptions,
  adminGetSettings,
  adminPutSettings,
  type AdminSettings,
  type AdminOptions,
} from "@/lib/api";
import { API_URL } from "@/lib/constants";

const TOKEN_KEY = "admin_token";

export default function AdminPage() {
  // Auth state
  const [token, setToken] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);

  // Settings state
  const [options, setOptions] = useState<AdminOptions | null>(null);
  const [settings, setSettings] = useState<AdminSettings | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Restore token from sessionStorage on mount
  useEffect(() => {
    const stored = sessionStorage.getItem(TOKEN_KEY);
    if (stored) setToken(stored);
  }, []);

  // Load options + settings once we have a token
  useEffect(() => {
    if (!token) return;
    Promise.all([adminGetOptions(token), adminGetSettings(token)])
      .then(([opts, setts]) => {
        setOptions(opts);
        setSettings(setts);
      })
      .catch(() => {
        // Token may be expired – force re-login
        setToken(null);
        sessionStorage.removeItem(TOKEN_KEY);
      });
  }, [token]);

  // ── Login ────────────────────────────────────────────────────────────────

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoginLoading(true);
    setLoginError(null);
    try {
      const { token: t } = await adminLogin(password);
      sessionStorage.setItem(TOKEN_KEY, t);
      setToken(t);
      setPassword("");
    } catch (err: unknown) {
      if (err instanceof Error) {
        if (err.message.includes("API 401")) {
          setLoginError("Invalid password");
        } else if (err.message.includes("API 404")) {
          setLoginError(
            `Admin endpoint not found on backend (${API_URL}). Ensure the backend is running the latest code and has /api/admin/login.`
          );
        } else {
          setLoginError(err.message);
        }
      } else {
        setLoginError("Login failed");
      }
    } finally {
      setLoginLoading(false);
    }
  }

  // ── Save settings ────────────────────────────────────────────────────────

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !settings) return;
    setSaveLoading(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      const updated = await adminPutSettings(token, settings);
      setSettings(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaveLoading(false);
    }
  }

  function toggleChatType(type: string) {
    if (!settings) return;
    const current = settings.types_of_chat_list;
    const next = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type];
    setSettings({ ...settings, types_of_chat_list: next });
  }

  // ── Render: login gate ───────────────────────────────────────────────────

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200">
        <div className="glass-panel p-10 w-full max-w-sm space-y-6">
          <h1 className="text-2xl font-bold text-brand-dark text-center">Admin Access</h1>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-dark"
                autoFocus
                required
              />
            </div>
            {loginError && (
              <p className="text-sm text-red-600">{loginError}</p>
            )}
            <button
              type="submit"
              disabled={loginLoading}
              className="w-full bg-brand-dark text-white rounded-lg py-2 text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition"
            >
              {loginLoading ? "Logging in…" : "Log In"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // ── Render: loading ──────────────────────────────────────────────────────

  if (!options || !settings) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Loading settings…
      </div>
    );
  }

  // ── Render: settings panel ───────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-start justify-center py-16 px-4">
      <div className="glass-panel p-10 w-full max-w-lg space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-brand-dark">Admin Settings</h1>
          <button
            onClick={() => {
              sessionStorage.removeItem(TOKEN_KEY);
              setToken(null);
            }}
            className="text-xs text-gray-400 hover:text-gray-600 transition"
          >
            Log out
          </button>
        </div>

        <p className="text-sm text-gray-500 -mt-4">
          Changes apply immediately and persist until the server is restarted.
        </p>

        <form onSubmit={handleSave} className="space-y-8">

          {/* 1 · Chat types */}
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-gray-800">
              Active chat types
            </legend>
            <p className="text-xs text-gray-500">
              Select which chat types are assigned to new sessions. At least one must be selected.
            </p>
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              Changes apply to new chats and sessions that have not started chatting yet. Chats already in progress keep their current chat type.
            </p>
            <div className="space-y-2">
              {options.allowed_chat_types.map((type) => (
                <label
                  key={type}
                  className="flex items-center gap-3 cursor-pointer select-none"
                >
                  <input
                    type="checkbox"
                    checked={settings.types_of_chat_list.includes(type)}
                    onChange={() => toggleChatType(type)}
                    className="w-4 h-4 accent-brand-dark"
                  />
                  <span className="text-sm text-gray-700">{type}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {/* 2 · Similarity with friends */}
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-gray-800">
              Persona matching mode (SIMILARITY_WITH_FRIENDS)
            </legend>
            <p className="text-xs text-gray-500">
              <strong>Disabled:</strong> rank by cosine similarity only.{" "}
              <strong>Friends:</strong> pre-filter by joint accounts, then rank by joint categories/users → similarity.{" "}
              <strong>Combined:</strong> first filter by similarity threshold, then rank by joint categories/users → similarity.
            </p>
            <div className="flex gap-6">
              {(options.allowed_similarity_modes ?? ["disabled", "friends", "combined"]).map((mode) => (
                <label key={mode} className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="radio"
                    name="similarity_with_friends"
                    checked={settings.similarity_with_friends === mode}
                    onChange={() => setSettings({ ...settings, similarity_with_friends: mode })}
                    className="w-4 h-4 accent-brand-dark"
                  />
                  <span className="text-sm text-gray-700 capitalize">{mode}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {/* 2b · Similarity threshold (only relevant for combined mode) */}
          {settings.similarity_with_friends === "combined" && (
            <fieldset className="space-y-3">
              <legend className="text-sm font-semibold text-gray-800">
                Similarity threshold
              </legend>
              <p className="text-xs text-gray-500">
                Only personas with cosine similarity above this value are considered (combined mode).
              </p>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={settings.similarity_threshold}
                  onChange={(e) => setSettings({ ...settings, similarity_threshold: parseFloat(e.target.value) })}
                  className="flex-1 accent-brand-dark"
                />
                <span className="text-sm font-mono text-gray-700 w-12 text-right">
                  {settings.similarity_threshold.toFixed(2)}
                </span>
              </div>
            </fieldset>
          )}

          {/* 3 · Persona bank */}
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-gray-800">
              Persona bank
            </legend>
            <p className="text-xs text-gray-500">
              <strong>New (v3):</strong> latest curated persona set.{" "}
              <strong>Old (v2):</strong> previous persona set. Switching reloads
              the file into memory immediately — active chats are unaffected.
            </p>
            <div className="flex gap-6">
              {(options.allowed_persona_banks ?? ["v3", "v2"]).map((bank) => {
                const label = bank === "v3" ? "New Persona Bank" : "Old Persona Bank";
                return (
                  <label key={bank} className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="radio"
                      name="persona_bank"
                      checked={settings.persona_bank === bank}
                      onChange={() => setSettings({ ...settings, persona_bank: bank })}
                      className="w-4 h-4 accent-brand-dark"
                    />
                    <span className="text-sm text-gray-700">{label}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          {/* 4 · OpenAI model */}
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-gray-800">
              OpenAI model
            </legend>
            <p className="text-xs text-gray-500">
              Model used for both the main chat and intent classification. Changes take effect for
              the next request.
            </p>
            <select
              value={settings.openai_model}
              onChange={(e) => setSettings({ ...settings, openai_model: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-dark"
            >
              {options.allowed_models.map((model) => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
          </fieldset>

          {/* 5 · Debug mode */}
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-gray-800">
              Debug mode
            </legend>
            <p className="text-xs text-gray-500">
              When enabled, the backend debug endpoints are active and the chat page shows the
              system-prompt, friends-info, and top-personas panels.
            </p>
            <div className="flex gap-6">
              {[true, false].map((val) => (
                <label key={String(val)} className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="radio"
                    name="debug"
                    checked={settings.debug === val}
                    onChange={() => setSettings({ ...settings, debug: val })}
                    className="w-4 h-4 accent-brand-dark"
                  />
                  <span className="text-sm text-gray-700">{val ? "Enabled" : "Disabled"}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Feedback */}
          {saveError && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">
              {saveError}
            </p>
          )}
          {saveSuccess && (
            <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-2">
              Settings saved successfully.
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={saveLoading || settings.types_of_chat_list.length === 0}
            className="w-full bg-brand-dark text-white rounded-lg py-2 text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition"
          >
            {saveLoading ? "Saving…" : "Save Settings"}
          </button>
        </form>
      </div>
    </div>
  );
}
