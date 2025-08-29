import React from 'react';

const Services = () => {
  return (
    <section className="bg-white text-gray-900">
      <div className="mx-auto max-w-screen-xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-lg text-center">
          <h2 className="text-3xl font-bold sm:text-4xl">Our Services</h2>
          <p className="mt-4 text-gray-500">
            We offer a range of services to help you create a winning resume.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
          <a
            className="block rounded-xl border border-gray-200 p-8 shadow-xl transition hover:border-pink-500/10 hover:shadow-pink-500/10"
            href="#"
          >
            <h3 className="mt-4 text-xl font-bold text-gray-900">Resume Analysis</h3>
            <p className="mt-1 text-sm text-gray-500">
              Our AI-powered platform analyzes your resume and provides detailed feedback on how to improve it.
            </p>
          </a>

          <a
            className="block rounded-xl border border-gray-200 p-8 shadow-xl transition hover:border-pink-500/10 hover:shadow-pink-500/10"
            href="#"
          >
            <h3 className="mt-4 text-xl font-bold text-gray-900">Keyword Optimization</h3>
            <p className="mt-1 text-sm text-gray-500">
              We help you optimize your resume with the right keywords to get past applicant tracking systems (ATS).
            </p>
          </a>

          <a
            className="block rounded-xl border border-gray-200 p-8 shadow-xl transition hover:border-pink-500/10 hover:shadow-pink-500/10"
            href="#"
          >
            <h3 className="mt-4 text-xl font-bold text-gray-900">Professional Templates</h3>
            <p className="mt-1 text-sm text-gray-500">
              Choose from a variety of professionally designed templates to create a resume that stands out.
            </p>
          </a>
        </div>
      </div>
    </section>
  );
};

export default Services;