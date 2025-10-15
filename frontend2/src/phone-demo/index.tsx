import React from "react";

type Props = {
  children?: React.ReactNode;
};

const PhoneDemo = ({ children }: Props) => {
  return (
    <div className="flex justify-center items-center p-6">
      <div className="relative rounded-[2.5rem] border-[12px] border-neutral-800 dark:border-neutral-200 w-[320px] h-[640px] bg-black shadow-2xl overflow-hidden">
        {/* Camera notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-6 bg-neutral-800 dark:bg-neutral-100 rounded-b-3xl z-10" />

        {/* Screen */}
        <div className="relative w-full h-full bg-white dark:bg-neutral-900 rounded-[1.5rem] overflow-hidden">
          {children ? (
            children
          ) : (
            <div className="flex h-full items-center justify-center text-neutral-500">
              Demo screen
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PhoneDemo;
