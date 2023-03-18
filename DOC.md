# The Dependency Inversion Principle

You might be familiar with the dependency inversion principle (DIP) already,
because it’s the D in SOLID.[2]

Unfortunately, we can’t illustrate the DIP by using three tiny code listings as
we did for encapsulation. However, the whole of [part1] is essentially a worked
example of implementing the DIP throughout an application, so you’ll get your
fill of concrete examples.

In the meantime, we can talk about DIP’s formal definition:

    High-level modules should not depend on low-level modules. Both should
    depend on abstractions.

    Abstractions should not depend on details. Instead, details should depend
    on abstractions.

High-level modules are the code that your organization really cares about.
Perhaps you work for a pharmaceutical company, and your high-level modules deal
with patients and trials. Perhaps you work for a bank, and your high-level
modules manage trades and exchanges. The high-level modules of a software
system are the functions, classes, and packages that deal with our real-world
concepts.

By contrast, low-level modules are the code that your organization doesn’t care
about. It’s unlikely that your HR department gets excited about filesystems or
network sockets. It’s not often that you discuss SMTP, HTTP, or AMQP with your
finance team. For our nontechnical stakeholders, these low-level concepts
aren’t interesting or relevant. All they care about is whether the high-level
concepts work correctly. If payroll runs on time, your business is unlikely to
care whether that’s a cron job or a transient function running on Kubernetes.

Depends on doesn’t mean imports or calls, necessarily, but rather a more
general idea that one module knows about or needs another module.

And we’ve mentioned abstractions already: they’re simplified interfaces that
encapsulate behavior, in the way that our duckduckgo module encapsulated a
search engine’s API.


# Service Layer Pattern

If we look at what our Flask app is doing, there’s quite a lot of what we might
call orchestration—fetching stuff out of our repository, validating our input
against database state, handling errors, and committing in the happy path. Most
of these things don’t have anything to do with having a web API endpoint (you’d
need them if you were building a CLI, for example; see [appendix_csvs]), and
they’re not really things that need to be tested by end-to-end tests.

It often makes sense to split out a service layer, sometimes called an
orchestration layer or a use-case layer.

The service layer delegates to the model layer


Typical service-layer functions have similar steps:

    We fetch some objects from the repository.

    We make some checks or assertions about the request against the current
    state of the world.

    We call a domain service.

    If all is well, we save/update any state we’ve changed.

Service Layer signature / Dependency Inversion Principle

    def allocate(
        orderid: str, sku: str, qty: int,
        uow: unit_of_work.AbstractUnitOfWork
    )

    The signature depends on primitive type, so that service layer tests are
    fully decoupled from the model layer

    The signature depends on an abstraction, which is at the core of DIP. And
    the details of the implementation for our specific choice of persistent
    storage also depend on that same abstraction. 


# Unit of Work Pattern

The Unit of Work pattern is an abstraction around data integrity

    It helps to enforce the consistency of our domain model, and improves
    performance, by letting us perform a single flush operation at the end of
    an operation.

It works closely with the Repository and Service Layer patterns

    The Unit of Work pattern completes our abstractions over data access by
    representing atomic updates. Each of our service-layer use cases runs in a
    single unit of work that succeeds or fails as a block.

This is a lovely case for a context manager

    Context managers are an idiomatic way of defining scope in Python. We can
    use a context manager to automatically roll back our work at the end of a
    request, which means the system is safe by default.

SQLAlchemy already implements this pattern

    We introduce an even simpler abstraction over the SQLAlchemy Session object
    in order to "narrow" the interface between the ORM and our code. This helps
    to keep us loosely coupled.


# Aggregate / Bounded Context

Aggregates, Bounded Contexts, and Microservices

    One of the most important contributions from Evans and the DDD community is
    the concept of bounded contexts.

    In essence, this was a reaction against attempts to capture entire
    businesses into a single model. The word customer means different things to
    people in sales, customer service, logistics, support, and so on.
    Attributes needed in one context are irrelevant in another; more
    perniciously, concepts with the same name can have entirely different
    meanings in different contexts. Rather than trying to build a single model
    (or class, or database) to capture all the use cases, it’s better to have
    several models, draw boundaries around each context, and handle the
    translation between different contexts explicitly.

    This concept translates very well to the world of microservices, where each
    microservice is free to have its own concept of "customer" and its own
    rules for translating that to and from other microservices it integrates
    with.

    In our example, the allocation service has Product(sku, batches), whereas
    the ecommerce will have Product(sku, description, price, image_url,
    dimensions, etc). As a rule of thumb, your domain models should
    include only the data that they need for performing calculations.

    Whether or not you have a microservices architecture, a key consideration
    in choosing your aggregates is also choosing the bounded context that they
    will operate in. By restricting the context, you can keep your number of
    aggregates low and their size manageable.

One Aggregate = One Repository

    Once you define certain entities to be aggregates, we need to apply the
    rule that they are the only entities that are publicly accessible to the
    outside world. In other words, the only repositories we are allowed should
    be repositories that return aggregates.

    The rule that repositories should only return aggregates is the main place
    where we enforce the convention that aggregates are the only way into our
    domain model. Be wary of breaking it! 


Optimistic Concurrency with Version Numbers

    Optimistic concurrency: the default assumption is that everything will be
    fine when two users want to make changes to the database

    Pessimistic concurrency: the default assumption is that two users are going
    to cause conflicts, and we want to prevent conflicts in all cases, so we
    lock everything just to be safe

    We have our new aggregate, so we’ve solved the conceptual problem of
    choosing an object to be in charge of consistency boundaries. Let’s now
    spend a little time talking about how to enforce data integrity at the
    database level. Note

    We don’t want to hold a lock over the entire batches table, but how will we
    implement holding a lock over just the rows for a particular SKU?

    One answer is to have a single attribute on the Product model that acts as
    a marker for the whole state change being complete and to use it as the
    single resource that concurrent workers can fight over. If two transactions
    read the state of the world for batches at the same time, and both want to
    update the allocations tables, we force both to also try to update the
    version_number in the products table, in such a way that only one of them
    can win and the world stays consistent.

    The usual way to handle a failure is to retry the failed operation from the beginning

Aggregates are your entrypoints into the domain model

    By restricting the number of ways that things can be changed, we make the
    system easier to reason about.

Aggregates are in charge of a consistency boundary

    An aggregate’s job is to be able to manage our business rules about
    invariants as they apply to a group of related objects. It’s the
    aggregate’s job to check that the objects within its remit are consistent
    with each other and with our rules, and to reject changes that would break
    the rules.

Aggregates and concurrency issues go together

    When thinking about implementing these consistency checks, we end up
    thinking about transactions and locks. Choosing the right aggregate is
    about performance as well as conceptual organization of your domain.


# Tests

Don’t Mock What You Don’t Own

    Why do we feel more comfortable mocking the UoW than the session? Both of
    our fakes achieve the same thing: they give us a way to swap out our
    persistence layer so we can run tests in memory instead of needing to talk
    to a real database. The difference is in the resulting design.

    If we cared only about writing tests that run quickly, we could create
    mocks that replace SQLAlchemy and use those throughout our codebase. The
    problem is that Session is a complex object that exposes lots of
    persistence-related functionality. It’s easy to use Session to make
    arbitrary queries against the database, but that quickly leads to data
    access code being sprinkled all over the codebase. To avoid that, we want
    to limit access to our persistence layer so each component has exactly what
    it needs and nothing more.

    By coupling to the Session interface, you’re choosing to couple to all the
    complexity of SQLAlchemy. Instead, we want to choose a simpler abstraction
    and use that to clearly separate responsibilities. Our UoW is much simpler
    than a session, and we feel comfortable with the service layer being able
    to start and stop units of work.

    "Don’t mock what you don’t own" is a rule of thumb that forces us to build
    these simple abstractions over messy subsystems. This has the same
    performance benefit as mocking the SQLAlchemy session but encourages us to
    think carefully about our designs.

High and Low Gear

    Most of the time, when we are adding a new feature or fixing a bug, we
    don’t need to make extensive changes to the domain model. In these cases,
    we prefer to write tests against services because of the lower coupling and
    higher coverage.

    For example, when writing an add_stock function or a cancel_order feature,
    we can work more quickly and with less coupling by writing tests against
    the service layer.

    When starting a new project or when hitting a particularly gnarly problem,
    we will drop back down to writing tests against the domain model so we get
    better feedback and executable documentation of our intent.

    The metaphor we use is that of shifting gears. When starting a journey, the
    bicycle needs to be in a low gear so that it can overcome inertia. Once
    we’re off and running, we can go faster and more efficiently by changing
    into a high gear; but if we suddenly encounter a steep hill or are forced
    to slow down by a hazard, we again drop down to a low gear until we can
    pick up speed again.

Domain Layer Tests

    Write unit tests for domain layer

Service Layer Tests

    Write unit tests for service Layer

    Service layer functions are written with primitive type so that there is no
    coupling between service layers tests and the domain

    Service layer tests can drop full dependency on the service by using
    messages and the message bus instead (event handlers instead of service functions)

    Service Layer Tests provides an implementation of the UoW and repository
    abstractions


Recap: Rules of Thumb for Different Types of Test

Aim for one end-to-end test per feature

    This might be written against an HTTP API, for example. The objective is to
    demonstrate that the feature works, and that all the moving parts are glued
    together correctly.

Write the bulk of your tests against the service layer

    These edge-to-edge tests offer a good trade-off between coverage, runtime,
    and efficiency. Each test tends to cover one code path of a feature and use
    fakes for I/O. This is the place to exhaustively cover all the edge cases
    and the ins and outs of your business logic.[1]

Maintain a small core of tests written against your domain model

    These tests have highly focused coverage and are more brittle, but they
    have the highest feedback. Don’t be afraid to delete these tests if the
    functionality is later covered by tests at the service layer.

Error handling counts as a feature

    Ideally, your application will be structured such that all errors that
    bubble up to your entrypoints (e.g., Flask) are handled in the same way.
    This means you need to test only the happy path for each feature, and to
    reserve one end-to-end test for all unhappy paths (and many unhappy path
    unit tests, of course).



# Domain Events and the Message Bus

Events can help with the single responsibility principle

    Code gets tangled up when we mix multiple concerns in one place. Events can
    help us to keep things tidy by separating primary use cases from secondary
    ones. We also use events for communicating between aggregates so that we
    don’t need to run long-running transactions that lock against multiple
    tables.

A message bus routes messages to handlers

    You can think of a message bus as a dict that maps from events to their
    consumers. It doesn’t "know" anything about the meaning of events; it’s
    just a piece of dumb infrastructure for getting messages around the system.

Option 1: Service layer raises events and passes them to message bus

    The simplest way to start using events in your system is to raise them from
    handlers by calling bus.handle(some_new_event) after you commit your unit
    of work.

Option 2: Domain model raises events, service layer passes them to message bus

    The logic about when to raise an event really should live with the model,
    so we can improve our system’s design and testability by raising events
    from the domain model. It’s easy for our handlers to collect events off the
    model objects after commit and pass them to the bus.

Option 3: UoW collects events from aggregates and passes them to message bus

    Adding bus.handle(aggregate.events) to every handler is annoying, so we can
    tidy up by making our unit of work responsible for raising events that were
    raised by loaded objects. This is the most complex design and might rely on
    ORM magic, but it’s clean and easy to use once it’s set up.

# Project structure

Domain

    Let’s have a folder for our domain model. Currently that’s just one file,
    but for a more complex application, you might have one file per class; you
    might have helper parent classes for Entity, ValueObject, and Aggregate,
    and you might add an exceptions.py for domain-layer exceptions

Service Layer

    We’ll distinguish the service layer. Currently that’s just one file called
    services.py for our service-layer functions. You could add service-layer
    exceptions here

Adapters

    Adapters is a nod to the ports and adapters terminology. This will fill up
    with any other abstractions around external I/O (e.g., a redis_client.py).
    Strictly speaking, you would call these secondary adapters or driven
    adapters, or sometimes inward-facing adapters.

Entrypoints

    Entrypoints are the places we drive our application from. In the official
    ports and adapters terminology, these are adapters too, and are referred to
    as primary, driving, or outward-facing adapters.

What about ports? As you may remember, they are the abstract interfaces that
the adapters implement. We tend to keep them in the same file as the adapters
that implement them.
