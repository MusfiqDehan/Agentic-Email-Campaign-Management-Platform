import axios from '@/config/axios';
import type { Package } from './admin';

export type { Package };

export interface PackageCatalog {
  current_package: Package | null;
  plan_type: string;
  is_starter: boolean;
  can_upgrade: boolean;
  available_upgrades: Package[];
}

export interface PackageUpgradeResult extends PackageCatalog {
  changed: boolean;
  effective_limits: Record<string, number | boolean | null>;
}

export const fetchPackageCatalog = async (): Promise<PackageCatalog> => {
  const response = await axios.get('/campaigns/packages/catalog/');
  return response.data.data;
};

export const upgradePackage = async (packageId: string): Promise<PackageUpgradeResult> => {
  const response = await axios.post('/campaigns/packages/upgrade/', {
    package_id: packageId,
  });
  return response.data.data;
};
