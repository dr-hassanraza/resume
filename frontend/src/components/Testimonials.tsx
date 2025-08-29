import React from 'react';

const Testimonials = () => {
  return (
    <section className="bg-white text-gray-900">
      <div className="mx-auto max-w-screen-xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-lg text-center">
          <h2 className="text-3xl font-bold sm:text-4xl">What Our Customers Say</h2>
          <p className="mt-4 text-gray-500">
            Read what our satisfied customers have to say about our service.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-lg">
            <p className="text-lg font-medium text-gray-900">
              "The best resume builder I've ever used. I got a job in less than a week!"
            </p>
            <p className="mt-4 text-sm text-gray-500">- John Doe</p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-lg">
            <p className="text-lg font-medium text-gray-900">
              "I was able to create a professional resume in minutes. Highly recommended!"
            </p>
            <p className="mt-4 text-sm text-gray-500">- Jane Smith</p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-lg">
            <p className="text-lg font-medium text-gray-900">
              "I love the real-time feedback feature. It helped me improve my resume a lot."
            </p>
            <p className="mt-4 text-sm text-gray-500">- Peter Jones</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Testimonials;