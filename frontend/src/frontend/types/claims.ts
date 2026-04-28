export type UserProfile = {
  id: string; // same as oid etc.
  '@odata.context': string;
  businessPhones: string[];
  userPrincipalName: string;
  displayName: string;
  givenName: string;
  surname: string;
  jobTitle: string;
  mail: string;
  email?: string;
  mobilePhone: string;
  officeLocation: string;
  preferredLanguage: string;
};

export type Group = {
  '@odata.type': string;
  id: string;
  displayName: string | null;
  description: string | null;
  uniqueName: string | null;
  [key: string]: unknown | null;
};

export type Groups = {
  '@odata.context': string;
  value: Group[];
};

export type AzureProfileResponse = {
  user: UserProfile;
  groups: Groups;
};

export type AzureClaims = {
  exp: number;
  iat: number;
  nbf: number;
  sub: string;
  given_name: string;
  unique_name: string; // email
  oid: string;
};
