import React from "react";
import dynamic from "next/dynamic";
import Head from "next/head";
import { Toaster } from "react-hot-toast";

// Dynamically load form component to avoid SSR hydration issues
const AlarmForm = dynamic(
  () => import("../components/AlarmForm"),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse">
          <div className="h-12 w-12 bg-blue-400 rounded-full"></div>
        </div>
      </div>
    ),
  }
);

export default function Home() {
  return (
    <>
      <Head>
        <title>Financial Alarm System</title>
        <meta name="description" content="Smart financial price alerts for crypto, forex, and stocks" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        {/* Page Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-12 shadow-lg">
          <div className="container mx-auto px-4">
            <div className="text-center">
              <h1 className="text-4xl font-bold mb-2">
                Financial Alarm System
              </h1>
              <p className="text-blue-100 text-lg">
                Get instant notifications when your price targets are reached
              </p>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="container mx-auto px-4 py-12 max-w-2xl">
          {/* Asset Class Information Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
              <div className="text-2xl mb-2">Crypto</div>
              <h3 className="font-semibold text-gray-900 mb-1">Cryptocurrency</h3>
              <p className="text-sm text-gray-600">Bitcoin, Ethereum and more</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
              <div className="text-2xl mb-2">Forex</div>
              <h3 className="font-semibold text-gray-900 mb-1">Currency Pairs</h3>
              <p className="text-sm text-gray-600">Exchange rates and currency pairs</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
              <div className="text-2xl mb-2">Stocks</div>
              <h3 className="font-semibold text-gray-900 mb-1">Equities</h3>
              <p className="text-sm text-gray-600">Global stocks and indexes</p>
            </div>
          </div>

          {/* Alarm Creation Form Card */}
          <div className="bg-white rounded-xl shadow-xl overflow-hidden border border-gray-200">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-4">
              <h2 className="text-xl font-bold text-white">
                Create New Alarm
              </h2>
              <p className="text-blue-100 text-sm mt-1">
                Set up price alerts with multiple monitoring conditions
              </p>
            </div>

            <div className="p-8">
              <AlarmForm />
            </div>
          </div>

          {/* Footer Information */}
          <div className="mt-8 text-center text-gray-600 text-sm">
            <p>Real-time monitoring • Email notifications • Instant alerts</p>
          </div>
        </div>
      </main>

      <Toaster position="top-right" />
    </>
  );
}