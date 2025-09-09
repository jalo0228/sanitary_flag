// This function runs every 500ms to check for changes on the page.
setInterval(injectCustomInfo, 500);

function injectCustomInfo() {
  // 1. Find the rating section, which we'll use as an anchor to insert our HTML.
  const ratingSection = document.querySelector('div.F7nice');

  // 2. If the rating section exists AND our custom HTML hasn't been added yet, run the code.
  if (ratingSection && !document.getElementById('my-review-summary')) {

    // 3. Get the restaurant's name and address.
    const placeName = document.querySelector('h1.jKLs2d')?.textContent || "Name not found";
    // The address is usually in a button with an aria-label that starts with "Address: "
    const placeAddress = document.querySelector('button[aria-label^="Address: "]')?.textContent.replace('Address: ', '') || "Address not found";

    console.log(`Place: ${placeName}`);
    console.log(`Address: ${placeAddress}`);

    // 4. Define the Flag and Comment. (Later, this data can come from a server!)
    const flagEmoji = '🟢'; // Can be changed to 🔴 or 🟡
    const summaryComment = "Overall a fantastic experience. The fresh ingredients and friendly service were particularly impressive. Reservations might be needed during dinner hours.";

    // 5. Create our custom HTML snippet, styled to match Google's UI.
    const customHtml = `
      <div id="my-review-summary" style="padding: 16px 0px; display: flex; align-items: flex-start; font-size: 14px; border-top: 1px solid #e0e0e0;">
        <div style="font-size: 24px; margin-right: 16px; margin-top: -2px;">${flagEmoji}</div>
        <div>
          <div style="font-weight: 500; color: #202124; margin-bottom: 4px;">AI Summary</div>
          <div style="color: #5f6368; line-height: 1.4;">${summaryComment}</div>
        </div>
      </div>
    `;

    // 6. Insert our custom HTML right after the rating section.
    ratingSection.insertAdjacentHTML('afterend', customHtml);

    console.log("AI Summary injected successfully!");
  }
}