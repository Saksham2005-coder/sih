import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export const AppLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-brand-porcelain text-brand-ink flex flex-col transition-colors duration-150">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-8 overflow-y-auto max-w-7xl text-brand-ink">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
