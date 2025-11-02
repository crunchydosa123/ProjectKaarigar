This is an LLM Context for frontend2. 

Frontend2 is a React (TypeScript) App created with Vite. We have used shadcn components which you will be able to see in /src/components/ui. Some other components are present in /src/components/custom.

# Layout
This entire react app is on a single page. This website is meant as a demo for a mobile app, but we will be using web dev technologies. In order to avoid changing routes, a single page (App.tsx) is present.   

## PageContext
App.tsx has two parts of a screen. The left side is PhoneDemo whose parent element is present in src/phone-demo/index.tsx. Instead of routing, the entire app uses PageContext to manage the current page. PageContext is present at /src/contexts/PageContext and allows you to get and set the current page.

## PhoneLayout
PhoneLayout is a layout file that mimics the outline of a phone with fixed width and height.

## index.tsx
All the routing of pages for the PhoneDemo is done at phone-demo/index.tsx. This file uses the PageContext and renders components inside the phone layout.

# Routing
Some features require more than one page. As such, we have used '/' in the currentPage to denote the same feature route. For eg:
```
create-content/logos
create-content/videos
```

# How to create a new page in the phone-demo  
1. Create a new component inside /src/phone-demo
2. Use this basic template:
  ```
  import { usePage } from '@/contexts/PageContext'
  import { House } from 'lucide-react';
  import { useState } from 'react';

    const {YourComponent} = () => {
    const { setCurrentPage } = usePage();
    return (

    <div
        className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
        style={{ backgroundImage: "url('/white_bg.png')" }}
      >
        {/* Header */}
        <div className="w-full mt-10 flex justify-start items-center p-3">
          <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('home')}><House /></button>
          <div className="text-md font-bold ml-3">Create Content with AI</div>
        </div>
      {/*Your Main code starts from here*/}
    </div>
    )
    }
  ```
3. Populate your main content here. DO NOT MAKE ANY OTHER EXTRA COMPONENT. ADD ALL CODE FOR A SINGLE 'PAGE' IN A SINGLE COMPONENT. DO NOT DISREGARD THIS.
4. Use a page string and add it to src/phone-demo/index.tsx with conditionally rendering the component you just created like this:
  ```
    {currentPage === "your-route/page1" && <YourComponent />}
  ```
4. Import the component in the file as well.

# Changes made by LLM
After you make any changes, append them here and refer to them.
