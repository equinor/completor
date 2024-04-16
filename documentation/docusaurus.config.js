// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config

import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Completor Documentation',
  tagline: 'Inflow Control Modelling',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://equinor.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'equinor', // Usually your GitHub org/user name.
  projectName: 'completor', // Usually your repo name.
  deploymentBranch: 'gh-pages',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/equinor/completor/tree/main/documentation',
          routeBasePath: "/",
        },
        blog: false,
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/completor.png',
      navbar: {
        title: '',
        logo: {
          alt: 'Completor logo',
          src: 'img/completor.png',
        },
        items: [
          {
            href: 'https://github.com/equinor/completor',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Tutorial',
                to: '/',
              },
            ],
          },
          {
            title: 'Contact',
            items: [
              {
                label: 'Support Email',
                href: 'mailto:fg_InflowControlSoftware@equinor.com',
              },
              {
                label: 'Slack - Internal',
                href: 'https://equinor.slack.com/archives/C02MVVAC9L4',
              },
              {
                label: 'Engage (Yammer) - Internal',
                href: 'https://engage.cloud.microsoft/main/groups/eyJfdHlwZSI6Ikdyb3VwIiwiaWQiOiI4NjI2OTE3Mzc2MCJ9/all?domainRedirect=true',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/equinor/completor',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Equinor ASA. Built with Docusaurus.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
};

export default config;
