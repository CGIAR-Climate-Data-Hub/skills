import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://cgiar-climate-data-hub.github.io',
  base: '/skills',
  integrations: [
    starlight({
      title: 'CDH Skills',
      description: 'AI-powered climate data workflows for agriculture and climate research.',
      logo: {
        src: './src/assets/cgiar-climate-action-logo.png',
        alt: 'CGIAR Climate Action',
        replacesTitle: false,
      },
      customCss: ['./src/styles/custom.css'],
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/CGIAR-Climate-Data-Hub/skills' },
      ],
      editLink: {
        baseUrl: 'https://github.com/CGIAR-Climate-Data-Hub/skills/edit/main/docs-site/src/content/docs/',
      },
      sidebar: [
        {
          label: 'Overview',
          items: [
            { label: 'Getting started', slug: 'getting-started' },
          ],
        },
        {
          label: 'Skills',
          items: [
            { label: 'GCF Pipeline', slug: 'skills/gcf-pipeline' },
            { label: 'Climate Data Download', slug: 'skills/climate-data-download' },
            { label: 'Geospatial Cube Processor', slug: 'skills/geospatial-cube-processor' },
            { label: 'Notebook Plots', slug: 'skills/notebook-plots' },
            { label: 'Climate Dashboard', slug: 'skills/climate-dashboard' },
          ],
        },
        {
          label: 'Setup',
          items: [
            { label: 'Claude Code', slug: 'usage/claude-code' },
            { label: 'Antigravity', slug: 'usage/antigravity' },
            { label: 'OpenAI Codex', slug: 'usage/codex' },
          ],
        },
      ],
    }),
  ],
});
