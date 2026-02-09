/**
 * GitHub Actions script to automatically update the spam list by querying PRs
 * 
 * This script:
 * - Identifies spam users from closed unmerged PRs with 'spam' label
 * - Identifies rehabilitated users from merged PRs with 'Good First Issue' label
 * - Updates the spam list file based on most recent activity
 */

const fs = require('fs').promises;

const SPAM_LIST_PATH = '.github/spam-list.txt';
const dryRun = (process.env.DRY_RUN || 'false').toString().toLowerCase() === 'true';

// Load current spam list and compute updates based on spam vs rehabilitated users

async function computeSpamListUpdates(spamUsers, rehabilitatedUsers) {
  let currentSpamList = [];
  
  try {
    const content = await fs.readFile(SPAM_LIST_PATH, 'utf8');
    currentSpamList = content
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0);
  } catch (error) {
    if (error.code !== 'ENOENT') {
      throw error;
    }
    // File doesn't exist yet, start with empty list
  }
  
  const additions = [];
  const removals = [];
  const finalSpamList = new Set(currentSpamList);
  
  // Process spam users
  for (const [username, spamDate] of spamUsers.entries()) {
    const rehabDate = rehabilitatedUsers.get(username);
    
    if (!rehabDate || spamDate > rehabDate) {
      // User is spam (either never rehabilitated or spammed after rehabilitation)
      if (!finalSpamList.has(username)) {
        additions.push(username);
        finalSpamList.add(username);
      }
    }
  }
  
  // Process rehabilitated users
  for (const [username, rehabDate] of rehabilitatedUsers.entries()) {
    const spamDate = spamUsers.get(username);
    
    if (!spamDate || rehabDate > spamDate) {
      // User is rehabilitated (merged PR more recent than spam)
      if (finalSpamList.has(username)) {
        removals.push(username);
        finalSpamList.delete(username);
      }
    }
  }
  
  // Sort additions and removals alphabetically
  additions.sort((a, b) => a.localeCompare(b));
  removals.sort((a, b) => a.localeCompare(b));
  
  return {
    additions,
    removals,
    finalSpamList: Array.from(finalSpamList).sort((a, b) => a.localeCompare(b))
  };
}


function generateSummary(additions, removals) {
  const title = `Update spam list (${additions.length} additions, ${removals.length} removals)`;
  
  let body = '## Automated Spam List Update\n\n';
  body += 'This issue details the updates to the spam list based on recent PR activity.\n\n';
  
  if (additions.length > 0) {
    body += `### ➕ Additions (${additions.length})\n\n`;
    body += 'The following users were added to the spam list:\n\n';
    for (const username of additions) {
      body += `- ${username}\n`;
    }
    body += '\n';
  }
  
  if (removals.length > 0) {
    body += `### ➖ Removals (${removals.length})\n\n`;
    body += 'The following users were removed from the spam list (rehabilitated):\n\n';
    for (const username of removals) {
      body += `- ${username}\n`;
    }
    body += '\n';
  }
  
  if (additions.length === 0 && removals.length === 0) {
    body += '### ℹ️ No Changes\n\n';
    body += 'No updates were needed for the spam list.\n';
  }
  
  return { title, body };
}

// Main function to orchestrate the spam list update
 
module.exports = async ({github, context, core}) => {
  const { owner, repo } = context.repo;
  try {
    console.log('Starting spam list update...');
    
    if (dryRun) {
      console.log('⚠️  Running in DRY RUN mode - no files will be modified');
    }

    const spamUsers = new Map();
    const rehabilitatedUsers = new Map();

    const searches = [
      {
        name: 'spam PRs',
        query: `repo:${owner}/${repo} is:pr is:closed -is:merged label:spam`,
        process: async (pr) => {
          if (!pr.user?.login) {
            console.log(`Skipping PR #${pr.number}: user account unavailable`);
            return;
          }
          const username = pr.user.login;
          const closedDate = new Date(pr.closed_at);

          if (!spamUsers.has(username) || closedDate > spamUsers.get(username)) {
            spamUsers.set(username, closedDate);
          }
        }
      },
      {
        name:  'rehabilitated PRs',
        query: `repo:${owner}/${repo} is:pr is:merged label:"Good First Issue"`,
        process: async (pr) => {
         if (!pr.user?.login) {
            console.log(`Skipping PR #${pr.number}: user account unavailable`);
            return;
          }
          const username = pr.user.login;

          // Get the actual PR to find merge date
          const { data: prData } = await github.rest.pulls.get({
            owner,
            repo,
            pull_number: pr.number
          });

          if (prData.merged_at) {
            const mergeDate = new Date(prData.merged_at);

            if (!rehabilitatedUsers.has(username) || mergeDate > rehabilitatedUsers.get(username)) {
              rehabilitatedUsers.set(username, mergeDate);
            }
          }
        }
      }
    ];

    // Use pagination iterator with your existing pattern
    for (const { name, query, process } of searches) {
      console.log(`Fetching ${name}...`);
      
      const iterator = github.paginate.iterator(
        github.rest.search.issuesAndPullRequests,
        {
          q: query,
          per_page: 100,
          sort: 'updated',
          order: 'desc'
        }
      );

      for await (const { data: items } of iterator) {
        for (const pr of items) {
          // Sequential processing keeps API pressure predictable
          // eslint-disable-next-line no-await-in-loop
          await process(pr);
        }
      }
    }

    // After processing all PRs, compute the final spam list updates
    const { additions, removals } = await computeSpamListUpdates(
      spamUsers,
      rehabilitatedUsers
    );
    
    console.log(`Additions: ${additions.length}`);
    console.log(`Removals: ${removals.length}`);
    
    const { title, body } = generateSummary(additions, removals);
    const hasChanges = additions.length > 0 || removals.length > 0;
    
    if (hasChanges) {
      if (dryRun) {
        console.log('[DRY RUN] Would create issue with:');
        console.log(`Title: ${title}`);
        console.log(`Body: ${body}`);
      } else {
        // Check for existing open issue to avoid duplicates
        const { data: existing } = await github.rest.issues.listForRepo({
          owner,
          repo,
          labels: 'spam-list-update',
          state: 'open',
          per_page: 1
        });
        if (existing.length > 0) {
          console.log(`Skipping issue creation: open issue #${existing[0].number} already exists`);
          return;
        }
        await github.rest.issues.create({
          owner,
          repo,
          title,
          body,
          labels: ['spam-list-update', 'automated']
        });
        console.log('Issue created successfully');
      }
    } else {
      console.log('No changes needed, skipping issue creation');
    }
    
  } catch (error) {
    core.setFailed(`Failed to update spam list: ${error.message}`);
    throw error;
  }
};